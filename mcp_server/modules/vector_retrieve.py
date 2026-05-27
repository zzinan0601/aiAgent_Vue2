import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from modules.model_loader import get_embedder
from config import mcp_settings

logger = logging.getLogger(__name__)

def vector_retrieve(query: str, top_k: int = None) -> list:
    top_k = top_k or mcp_settings.retrieve_top_k
    logger.info("[vector_retrieve] 시작 query=" + query[:50] + " top_k=" + str(top_k))

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
            cur.execute(sql, (vec_str, vec_str, top_k))
            rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    logger.info("[vector_retrieve] 검색 완료: " + str(len(rows)) + "건")
    for i, r in enumerate(rows):
        logger.info(
            "[vector_retrieve] 결과[" + str(i) + "]"
            " score=" + str(round(float(r.get("score", 0)), 4)) +
            " file=" + str(r.get("filename")) +
            " text=" + str(r.get("chunk_text", ""))[:80]
        )
    return rows
