import logging
from sqlalchemy.orm import Session
from models.models import Embedding, Document
from rag.model_loader import get_embedder

logger = logging.getLogger(__name__)

def get_embedding(text: str) -> list:
    model  = get_embedder()
    result = model.encode(
        [text], batch_size=1, max_length=512,
        return_dense=True, return_sparse=False, return_colbert_vecs=False
    )
    return result["dense_vecs"][0].tolist()

def embed_and_save(db: Session, doc_id: int, chunks: list):
    model   = get_embedder()
    results = model.encode(
        chunks, batch_size=16, max_length=512,
        return_dense=True, return_sparse=False, return_colbert_vecs=False
    )
    vectors = results["dense_vecs"]
    for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
        db.add(Embedding(
            doc_id=doc_id, chunk_text=chunk,
            embedding=vector.tolist(), chunk_index=idx
        ))
    doc             = db.query(Document).filter(Document.id == doc_id).first()
    doc.chunk_count = len(chunks)
    doc.status      = "done"
    db.commit()
    logger.info("[embedder] 완료 doc_id=" + str(doc_id) + " chunks=" + str(len(chunks)))
