from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from database import Base

class Session(Base):
    __tablename__ = "sessions"
    id            = Column(String(36), primary_key=True)
    title         = Column(String(200))
    system_prompt = Column(Text, default="")        # ← 추가
    few_shots     = Column(Text, default="[]")
    use_knowledge = Column(Boolean, default=False)
    temperature   = Column(Float, default=0.1)
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())
    messages      = relationship("Message", back_populates="session", cascade="all, delete")

class Message(Base):
    __tablename__ = "messages"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"))
    role       = Column(String(20), nullable=False)
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    session    = relationship("Session", back_populates="messages")

class Document(Base):
    __tablename__ = "documents"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    filename     = Column(String(300), nullable=False)
    file_path    = Column(String(500))
    chunk_count  = Column(Integer, default=0)
    status       = Column(String(20), default="pending")
    is_knowledge = Column(Boolean, default=False)
    doc_metadata = Column(JSONB, default=dict)
    created_at   = Column(DateTime, server_default=func.now())
    embeddings   = relationship("Embedding", back_populates="document", cascade="all, delete")

class Embedding(Base):
    __tablename__ = "embeddings"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    doc_id      = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_text  = Column(Text, nullable=False)
    embedding      = Column(Vector(1024))
    chunk_index    = Column(Integer)
    chunk_metadata = Column(JSONB, default=dict)
    created_at     = Column(DateTime, server_default=func.now())
    document       = relationship("Document", back_populates="embeddings")

# ── Sparse 역인덱스 (하이브리드 RAG) ──
class SparseIndex(Base):
    __tablename__ = "sparse_index"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    embedding_id = Column(Integer, ForeignKey("embeddings.id", ondelete="CASCADE"))
    token_id     = Column(Integer, nullable=False)
    weight       = Column(Float, nullable=False)

class RagSetting(Base):
    __tablename__ = "rag_settings"
    id             = Column(Integer, primary_key=True)
    chunk_size     = Column(Integer, default=500)
    chunk_overlap  = Column(Integer, default=50)
    retrieve_top_k = Column(Integer, default=10)
    rerank_top_n   = Column(Integer, default=3)
    dense_weight   = Column(Float, default=0.7)
    sparse_weight  = Column(Float, default=0.3)

def get_rag_settings(db) -> RagSetting:
    setting = db.query(RagSetting).first()
    if not setting:
        setting = RagSetting(id=1, chunk_size=500, chunk_overlap=50, retrieve_top_k=10, rerank_top_n=3, dense_weight=0.7, sparse_weight=0.3)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting
