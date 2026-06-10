import logging
from sqlalchemy.orm import Session
from models.models import Embedding, Document, SparseIndex
from rag.model_loader import get_embedder

logger = logging.getLogger(__name__)

def get_embedding(text: str) -> tuple:
    """Dense + Sparse 벡터를 함께 반환"""
    model  = get_embedder()
    result = model.encode(
        [text], batch_size=1, max_length=512,
        return_dense=True, return_sparse=True, return_colbert_vecs=False
    )
    dense_vec  = result["dense_vecs"][0].tolist()
    sparse_vec = _convert_sparse(result["lexical_weights"][0])
    return dense_vec, sparse_vec

def _convert_sparse(lexical_weight) -> dict:
    """BGE-M3 sparse 출력을 {token_id: weight} dict로 변환"""
    sparse = {}
    for token_id, weight in lexical_weight.items():
        w = float(weight)
        if w > 0.0:
            sparse[int(token_id)] = w
    return sparse

def embed_and_save(db: Session, doc_id: int, chunks: list, doc_metadata: dict = None):
    if doc_metadata is None:
        doc_metadata = {}
    
    model   = get_embedder()
    results = model.encode(
        chunks, batch_size=16, max_length=512,
        return_dense=True, return_sparse=True, return_colbert_vecs=False
    )
    dense_vecs  = results["dense_vecs"]
    sparse_vecs = results["lexical_weights"]

    for idx, (chunk, dense_vec, sparse_raw) in enumerate(zip(chunks, dense_vecs, sparse_vecs)):
        # 1. Dense 임베딩 저장
        emb = Embedding(
            doc_id=doc_id, chunk_text=chunk,
            embedding=dense_vec.tolist(), chunk_index=idx,
            chunk_metadata=doc_metadata
        )
        db.add(emb)
        db.flush()  # emb.id 확보

        # 2. Sparse 역인덱스 저장
        sparse_dict = _convert_sparse(sparse_raw)
        sparse_rows = [
            SparseIndex(embedding_id=emb.id, token_id=tid, weight=w)
            for tid, w in sparse_dict.items()
        ]
        if sparse_rows:
            db.bulk_save_objects(sparse_rows)

    doc             = db.query(Document).filter(Document.id == doc_id).first()
    doc.chunk_count = len(chunks)
    doc.status      = "done"
    db.commit()
    logger.info("[embedder] 완료 doc_id=" + str(doc_id) + " chunks=" + str(len(chunks)))
