import logging
import psycopg2
from collections import defaultdict
from psycopg2.extras import RealDictCursor
from modules.model_loader import get_embedder
from config import mcp_settings

logger = logging.getLogger(__name__)

# ── RRF 상수 ──
RRF_K = 60

def vector_retrieve(query: str, top_k: int = None, filters: dict = None) -> list:
    # 1. DB에서 실시간 RAG 설정 조회
    db_retrieve_top_k = top_k or mcp_settings.retrieve_top_k
    db_rerank_top_n   = mcp_settings.rerank_top_n
    dense_weight  = 0.7
    sparse_weight = 0.3

    conn = psycopg2.connect(**mcp_settings.db_dsn)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT retrieve_top_k, rerank_top_n, dense_weight, sparse_weight FROM rag_settings LIMIT 1")
            row = cur.fetchone()
            if row:
                db_retrieve_top_k = top_k or row[0]
                db_rerank_top_n   = row[1]
                dense_weight      = row[2] if row[2] is not None else 0.7
                sparse_weight     = row[3] if row[3] is not None else 0.3
    except Exception as e:
        logger.warning("[vector_retrieve] DB에서 RAG 설정 조회 실패: " + str(e))
    finally:
        conn.close()

    filter_sql = ""
    filter_params = []
    if filters:
        for k, v in filters.items():
            filter_sql += f" AND d.doc_metadata ->> '{k}' = %s"
            filter_params.append(str(v))

    logger.info("[vector_retrieve] 시작 query=" + query[:50] + " retrieve_top_k=" + str(db_retrieve_top_k))

    # 2. 쿼리 임베딩 (Dense + Sparse)
    logger.info("[vector_retrieve] 임베딩 중...")
    model   = get_embedder()
    result  = model.encode(
        [query], batch_size=1, max_length=512,
        return_dense=True, return_sparse=True, return_colbert_vecs=False
    )
    dense_vec = result["dense_vecs"][0].tolist()
    vec_str   = "[" + ",".join(map(str, dense_vec)) + "]"

    # 쿼리 Sparse 벡터 변환
    query_sparse = {}
    try:
        raw = result["lexical_weights"][0]
        for token_id, weight in raw.items():
            w = float(weight)
            if w > 0.0:
                query_sparse[int(token_id)] = w
    except Exception as e:
        logger.warning("[vector_retrieve] Sparse 벡터 변환 실패: " + str(e))

    logger.info("[vector_retrieve] 임베딩 완료 (sparse tokens: " + str(len(query_sparse)) + ")")

    dense_sql = f"""
        SELECT e.id AS emb_id, e.chunk_text, d.filename, d.doc_metadata,
               1 - (e.embedding <=> %s::vector) AS score
        FROM embeddings e
        JOIN documents d ON e.doc_id = d.id
        WHERE d.status = 'done' {filter_sql}
        ORDER BY e.embedding <=> %s::vector
        LIMIT %s
    """
    logger.info("[vector_retrieve] Dense 검색 중...")
    
    dense_query_params = [vec_str] + filter_params + [vec_str, db_retrieve_top_k]
    
    conn = psycopg2.connect(**mcp_settings.db_dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(dense_sql, tuple(dense_query_params))
            dense_rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    logger.info("[vector_retrieve] Dense 검색 완료: " + str(len(dense_rows)) + "건")

    # Dense 랭킹
    dense_rank = {}
    emb_map    = {}
    for rank, row in enumerate(dense_rows, 1):
        dense_rank[row["emb_id"]] = rank
        emb_map[row["emb_id"]]    = row

    # ── 4. Sparse 검색 (가중치가 0이면 스킵) ──
    sparse_rank = {}
    if query_sparse and sparse_weight > 0:
        query_token_ids = list(query_sparse.keys())
        placeholders = ",".join(["%s"] * len(query_token_ids))
        sparse_sql = f"""
            SELECT si.embedding_id, si.token_id, si.weight
            FROM sparse_index si
            JOIN embeddings e ON si.embedding_id = e.id
            JOIN documents d ON e.doc_id = d.id
            WHERE d.status = 'done' {filter_sql} AND si.token_id IN ({placeholders})
        """
        sparse_query_params = filter_params + query_token_ids
        conn = psycopg2.connect(**mcp_settings.db_dsn)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sparse_sql, tuple(sparse_query_params))
                sparse_rows = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

        # 청크별 Sparse 점수 집계
        sparse_scores = defaultdict(float)
        for row in sparse_rows:
            q_weight = query_sparse.get(row["token_id"], 0.0)
            sparse_scores[row["embedding_id"]] += q_weight * row["weight"]

        # Sparse 정렬 후 랭킹
        sorted_sparse = sorted(sparse_scores.items(), key=lambda x: x[1], reverse=True)
        for rank, (emb_id, _score) in enumerate(sorted_sparse[:db_retrieve_top_k], 1):
            sparse_rank[emb_id] = rank
        logger.info("[vector_retrieve] Sparse 검색 완료: " + str(len(sparse_scores)) + "건 매칭")

    # ── 5. RRF 점수 융합 ──
    all_emb_ids = set(dense_rank.keys()) | set(sparse_rank.keys())
    rrf_scores  = {}
    for emb_id in all_emb_ids:
        d_rank = dense_rank.get(emb_id, db_retrieve_top_k + 1)
        s_rank = sparse_rank.get(emb_id, db_retrieve_top_k + 1)
        rrf_scores[emb_id] = (
            dense_weight  * (1.0 / (RRF_K + d_rank)) +
            sparse_weight * (1.0 / (RRF_K + s_rank))
        )

    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    top_ids    = sorted_ids[:db_retrieve_top_k]

    # Dense에 없는 것은 DB 조회
    missing = [eid for eid in top_ids if eid not in emb_map]
    if missing:
        placeholders = ",".join(["%s"] * len(missing))
        extra_sql = f"""
            SELECT e.id AS emb_id, e.chunk_text, d.filename, d.doc_metadata, 0.0 AS score
            FROM embeddings e JOIN documents d ON e.doc_id = d.id
            WHERE e.id IN ({placeholders})
        """
        conn = psycopg2.connect(**mcp_settings.db_dsn)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(extra_sql, missing)
                for row in cur.fetchall():
                    emb_map[row["emb_id"]] = dict(row)
        finally:
            conn.close()

    rows = []
    for emb_id in top_ids:
        row = emb_map.get(emb_id)
        if row:
            doc_meta = row.get("doc_metadata") or {}
            row["summary"] = doc_meta.get("summary", "")
            row["last_modified_date"] = doc_meta.get("last_modified_date", "")
            row["score"] = rrf_scores.get(emb_id, 0.0)
            rows.append(row)

    logger.info("[vector_retrieve] RRF 융합 완료: " + str(len(rows)) + "건")

    # ── 6. BGE Reranker ──
    if rows and len(rows) > 1:
        try:
            from modules.model_loader import get_reranker
            reranker = get_reranker()
            pairs    = [[query, r["chunk_text"]] for r in rows]
            scores   = reranker.compute_score(pairs, normalize=True)
            for i, r in enumerate(rows):
                r["score"] = float(scores[i])
            rows.sort(key=lambda x: x["score"], reverse=True)
            logger.info("[vector_retrieve] BGE 리랭킹 완료")
        except Exception as e:
            logger.error("[vector_retrieve] 리랭킹 중 오류 발생: " + str(e))

    # 최종 결과
    final_results = rows[:db_rerank_top_n]
    for i, r in enumerate(final_results):
        logger.info(
            "[vector_retrieve] 최종 결과[" + str(i) + "]"
            " score=" + str(round(float(r.get("score", 0)), 4)) +
            " file=" + str(r.get("filename")) +
            " text=" + str(r.get("chunk_text", ""))[:80]
        )
    return final_results
