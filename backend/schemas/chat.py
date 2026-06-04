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
    system_prompt : Optional[str] = ""
    few_shots     : Optional[str] = "[]"
    use_knowledge : bool = False
    temperature   : float = 0.7
    created_at    : datetime
    updated_at    : datetime
    class Config:
        from_attributes = True

class UpdateSessionRequest(BaseModel):
    title         : Optional[str] = None
    system_prompt : Optional[str] = None
    few_shots     : Optional[str] = None
    use_knowledge : Optional[bool] = None
    temperature   : Optional[float] = None

class CreateSessionRequest(BaseModel):
    title         : Optional[str] = "새 채팅"
    use_knowledge : bool = False
    temperature   : Optional[float] = 0.7