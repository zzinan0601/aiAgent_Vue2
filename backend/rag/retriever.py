import logging
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import text
from rag.model_loader import get_embedder, get_reranker
from config import settings

logger = logging.getLogger(__name__)

# ── RRF 상수 ──
RRF_K = 60  # Reciprocal Rank Fusion 상수 (표준값)

def retrieve(db: Session, query: str, filters: dict = None) -> list:
    from models.models import get_rag_settings
    rag_settings = get_rag_settings(db)

    filter_sql = ""
    filter_params = {}
    if filters:
        for i, (k, v) in enumerate(filters.items()):
            p_key = f"f_{i}"
            filter_sql += f" AND d.doc_metadata ->> '{k}' = :{p_key}"
            filter_params[p_key] = str(v)

    model  = get_embedder()
    result = model.encode(
        [query], batch_size=1, max_length=512,
        return_dense=True, return_sparse=True, return_colbert_vecs=False
    )

    # ── 1. Dense 검색 ──
    dense_vec = result["dense_vecs"][0].tolist()
    vec_str   = "[" + ",".join(map(str, dense_vec)) + "]"

    dense_params = {"vec": vec_str, "k": rag_settings.retrieve_top_k}
    dense_params.update(filter_params)

    dense_sql = text(f"""
        SELECT e.id AS emb_id, e.chunk_text, d.filename, d.doc_metadata,
               1 - (e.embedding <=> :vec::vector) AS score
        FROM embeddings e JOIN documents d ON e.doc_id = d.id
        WHERE d.status = 'done' {filter_sql}
        ORDER BY e.embedding <=> :vec::vector LIMIT :k
    """)
    dense_rows = db.execute(dense_sql, dense_params).fetchall()
    logger.info("[retrieve] Dense 검색 완료: " + str(len(dense_rows)) + "건")

    # Dense 랭킹 (1-based)
    dense_rank = {}
    for rank, row in enumerate(dense_rows, 1):
        dense_rank[row.emb_id] = rank

    # ── 2. Sparse 검색 (가중치가 0이면 스킵) ──
    query_sparse = _get_query_sparse(result)
    sparse_rank  = {}

    if query_sparse and rag_settings.sparse_weight > 0:
        query_token_ids = list(query_sparse.keys())
        # sparse_index 테이블에서 쿼리 토큰에 매칭되는 청크 검색
        placeholders = ",".join([":t" + str(i) for i in range(len(query_token_ids))])
        sparse_sql = text(f"""
            SELECT si.embedding_id, si.token_id, si.weight
            FROM sparse_index si
            JOIN embeddings e ON si.embedding_id = e.id
            JOIN documents d ON e.doc_id = d.id
            WHERE d.status = 'done' {filter_sql} AND si.token_id IN ({placeholders})
        """)
        params = {"t" + str(i): tid for i, tid in enumerate(query_token_ids)}
        params.update(filter_params)
        sparse_rows = db.execute(sparse_sql, params).fetchall()

        # 청크별 Sparse 점수 집계 (dot product)
        sparse_scores = defaultdict(float)
        for row in sparse_rows:
            q_weight = query_sparse.get(row.token_id, 0.0)
            sparse_scores[row.embedding_id] += q_weight * row.weight

        # Sparse 점수 기준 정렬 후 랭킹
        sorted_sparse = sorted(sparse_scores.items(), key=lambda x: x[1], reverse=True)
        for rank, (emb_id, _score) in enumerate(sorted_sparse[:rag_settings.retrieve_top_k], 1):
            sparse_rank[emb_id] = rank
        logger.info("[retrieve] Sparse 검색 완료: " + str(len(sparse_scores)) + "건 매칭")

    # ── 3. RRF 점수 융합 ──
    all_emb_ids = set(dense_rank.keys()) | set(sparse_rank.keys())
    rrf_scores  = {}
    for emb_id in all_emb_ids:
        d_rank = dense_rank.get(emb_id, rag_settings.retrieve_top_k + 1)
        s_rank = sparse_rank.get(emb_id, rag_settings.retrieve_top_k + 1)
        rrf_scores[emb_id] = (
            rag_settings.dense_weight  * (1.0 / (RRF_K + d_rank)) +
            rag_settings.sparse_weight * (1.0 / (RRF_K + s_rank))
        )

    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    top_ids    = sorted_ids[:rag_settings.retrieve_top_k]

    # 후보 청크 텍스트 조회
    emb_map = {row.emb_id: row for row in dense_rows}
    # Dense에 없는 것은 DB 조회
    missing = [eid for eid in top_ids if eid not in emb_map]
    if missing:
        placeholders = ",".join([":m" + str(i) for i in range(len(missing))])
        extra_sql = text(f"""
            SELECT e.id AS emb_id, e.chunk_text, d.filename, d.doc_metadata, 0.0 AS score
            FROM embeddings e JOIN documents d ON e.doc_id = d.id
            WHERE e.id IN ({placeholders})
        """)
        params = {"m" + str(i): eid for i, eid in enumerate(missing)}
        for row in db.execute(extra_sql, params).fetchall():
            emb_map[row.emb_id] = row

    candidates = []
    for emb_id in top_ids:
        row = emb_map.get(emb_id)
        if row:
            doc_meta = getattr(row, 'doc_metadata', {}) or {}
            candidates.append({
                "text": row.chunk_text,
                "filename": row.filename,
                "summary": doc_meta.get("summary", ""),
                "last_modified_date": doc_meta.get("last_modified_date", ""),
                "rrf_score": rrf_scores[emb_id]
            })

    logger.info("[retrieve] RRF 융합 완료: " + str(len(candidates)) + "건 → Reranker 전달")

    # ── 4. Reranker ──
    return _rerank(query, candidates)[:rag_settings.rerank_top_n]


def _get_query_sparse(encode_result: dict) -> dict:
    """쿼리의 Sparse 벡터를 {token_id: weight} dict로 변환"""
    sparse = {}
    try:
        raw = encode_result["lexical_weights"][0]
        for token_id, weight in raw.items():
            w = float(weight)
            if w > 0.0:
                sparse[int(token_id)] = w
    except Exception as e:
        logger.warning("[retrieve] Sparse 벡터 변환 실패: " + str(e))
    return sparse


def _rerank(query: str, candidates: list) -> list:
    try:
        reranker = get_reranker()
        pairs    = [[query, c["text"]] for c in candidates]
        scores   = reranker.compute_score(pairs, normalize=True)
        for i, item in enumerate(candidates):
            item["score"] = float(scores[i])
        candidates.sort(key=lambda x: x["score"], reverse=True)
    except Exception as e:
        logger.error("[리랭크 실패] " + str(e))
    return candidates
