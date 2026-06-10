from pydantic import BaseModel
from datetime import datetime

class DocumentResponse(BaseModel):
    id          : int
    filename    : str
    chunk_count : int
    status      : str
    is_knowledge: bool = False
    created_at  : datetime
    class Config:
        from_attributes = True

class RagSettingsSchema(BaseModel):
    chunk_size: int
    chunk_overlap: int
    retrieve_top_k: int
    rerank_top_n: int
    dense_weight: float = 0.7
    sparse_weight: float = 0.3
    class Config:
        from_attributes = True