import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from modules.model_loader import get_embedder
from config import mcp_settings

logger = logging.getLogger(__name__)

def vector_retrieve(query: str, top_k: int = None) -> list:
    # 1. DB에서 실시간 RAG 설정 조회
    db_retrieve_top_k = top_k or mcp_settings.retrieve_top_k
    db_rerank_top_n = mcp_settings.rerank_top_n

    conn = psycopg2.connect(**mcp_settings.db_dsn)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT retrieve_top_k, rerank_top_n FROM rag_settings LIMIT 1")
            row = cur.fetchone()
            if row:
                db_retrieve_top_k = top_k or row[0]
                db_rerank_top_n = row[1]
    except Exception as e:
        logger.warning("[vector_retrieve] DB에서 RAG 설정 조회 실패: " + str(e))
    finally:
        conn.close()

    logger.info("[vector_retrieve] 시작 query=" + query[:50] + " retrieve_top_k=" + str(db_retrieve_top_k))

    logger.info("[vector_retrieve] 임베딩 중...")
    model   = get_embedder()
    result  = model.encode(
        [query], batch_size=1, max_length=512,
        return_dense=True, return_sparse=False, return_colbert_vecs=False
    )
    vec_str = "[" + ",".join(map(str, result["dense_vecs"][0].tolist())) + "]"
    logger.info("[vector_retrieve] 임베딩 완료")

    sql = """
        SELECT e.chunk_text, d.filename,
               1 - (e.embedding <=> %s::vector) AS score
        FROM embeddings e
        JOIN documents d ON e.doc_id = d.id
        WHERE d.status = 'done'
        ORDER BY e.embedding <=> %s::vector
        LIMIT %s
    """
    logger.info("[vector_retrieve] pgvector 검색 중...")
    conn = psycopg2.connect(**mcp_settings.db_dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (vec_str, vec_str, db_retrieve_top_k))
            rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    logger.info("[vector_retrieve] pgvector 검색 완료: " + str(len(rows)) + "건")

    # 2. BGE Reranker 모델로 리랭크 수행
    if rows and len(rows) > 1:
        try:
            from modules.model_loader import get_reranker
            reranker = get_reranker()
            pairs = [[query, r["chunk_text"]] for r in rows]
            scores = reranker.compute_score(pairs, normalize=True)
            for i, r in enumerate(rows):
                r["score"] = float(scores[i])
            rows.sort(key=lambda x: x["score"], reverse=True)
            logger.info("[vector_retrieve] BGE 리랭킹 완료")
        except Exception as e:
            logger.error("[vector_retrieve] 리랭킹 중 오류 발생: " + str(e))

    # 최종 결과 목록
    final_results = rows[:db_rerank_top_n]
    for i, r in enumerate(final_results):
        logger.info(
            "[vector_retrieve] 최종 결과[" + str(i) + "]"
            " score=" + str(round(float(r.get("score", 0)), 4)) +
            " file=" + str(r.get("filename")) +
            " text=" + str(r.get("chunk_text", ""))[:80]
        )
    return final_results
