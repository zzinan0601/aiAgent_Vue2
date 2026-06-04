import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from rag.model_loader import get_embedder, get_reranker
from config import settings

logger = logging.getLogger(__name__)

def retrieve(db: Session, query: str) -> list:
    from models.models import get_rag_settings
    rag_settings = get_rag_settings(db)

    model   = get_embedder()
    result  = model.encode(
        [query], batch_size=1, max_length=512,
        return_dense=True, return_sparse=False, return_colbert_vecs=False
    )
    vec_str = "[" + ",".join(map(str, result["dense_vecs"][0].tolist())) + "]"

    sql = text("""
        SELECT e.chunk_text, d.filename,
               1 - (e.embedding <=> :vec::vector) AS score
        FROM embeddings e JOIN documents d ON e.doc_id = d.id
        WHERE d.status = 'done'
        ORDER BY e.embedding <=> :vec::vector LIMIT :k
    """)
    rows = db.execute(sql, {"vec": vec_str, "k": rag_settings.retrieve_top_k}).fetchall()
    if not rows:
        return []

    candidates = [{"text": r.chunk_text, "filename": r.filename} for r in rows]
    return _rerank(query, candidates)[:rag_settings.rerank_top_n]

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
