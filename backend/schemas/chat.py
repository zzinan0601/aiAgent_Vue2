from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ChatRequest(BaseModel):
    session_id: str
    message   : str
    mode      : str = "auto"

class MessageResponse(BaseModel):
    id        : int
    role      : str
    content   : str
    created_at: datetime
    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    id            : str
    title         : Optional[str]
    system_prompt : Optional[str] = ""   # ← 추가
    created_at    : datetime
    updated_at    : datetime
    class Config:
        from_attributes = True

class CreateSessionRequest(BaseModel):
    title         : Optional[str] = "새 채팅"
    use_knowledge : bool = False           # ← 추가 (기본지식 사용 여부)