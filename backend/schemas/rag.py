from pydantic import BaseModel
from datetime import datetime

class DocumentResponse(BaseModel):
    id          : int
    filename    : str
    chunk_count : int
    status      : str
    is_knowledge: bool = False   # ← 추가
    created_at  : datetime
    class Config:
        from_attributes = True