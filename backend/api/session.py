import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.models import Session as SessionModel, Message, Document, Embedding
from schemas.chat import SessionResponse, CreateSessionRequest, MessageResponse

router = APIRouter()
logger = logging.getLogger(__name__)

def _build_system_prompt(db: Session) -> str:
    """기본지식 문서의 청크 전체를 system prompt로 빌드"""
    docs = db.query(Document).filter(
        Document.is_knowledge == True,
        Document.status == "done"
    ).all()

    if not docs:
        return ""

    parts = ["당신은 아래 업무 지식을 숙지한 AI 어시스턴트입니다.\n이 내용을 배경 지식으로 활용하여 답변하세요.\n"]

    for doc in docs:
        chunks = db.query(Embedding).filter(
            Embedding.doc_id == doc.id
        ).order_by(Embedding.chunk_index.asc()).all()

        if chunks:
            parts.append("=== " + doc.filename + " ===")
            parts.append("\n".join([c.chunk_text for c in chunks]))
            parts.append("")

    system_prompt = "\n".join(parts)
    logger.info("[session] system_prompt 빌드 완료: " + str(len(system_prompt)) + "자 / 문서 " + str(len(docs)) + "개")
    return system_prompt


@router.post("/", response_model=SessionResponse, summary="새 세션 생성")
def create_session(req: CreateSessionRequest, db: Session = Depends(get_db)):
    system_prompt = ""

    # 기본지식 사용 요청 시 system_prompt 빌드
    if req.use_knowledge:
        system_prompt = _build_system_prompt(db)
        if not system_prompt:
            logger.warning("[session] 기본지식 문서 없음 - 일반 채팅으로 생성")

    session = SessionModel(
        id            = str(uuid.uuid4()),
        title         = req.title,
        system_prompt = system_prompt
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/", response_model=list[SessionResponse], summary="세션 목록")
def list_sessions(db: Session = Depends(get_db)):
    return db.query(SessionModel).order_by(SessionModel.updated_at.desc()).all()


@router.get("/{session_id}/messages", response_model=list[MessageResponse], summary="대화 내용")
def get_messages(session_id: str, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    return db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at.asc()).all()


@router.delete("/{session_id}", summary="세션 삭제")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    db.delete(session)
    db.commit()
    return {"message": "삭제 완료"}


@router.patch("/{session_id}/title", summary="제목 수정")
def update_title(session_id: str, title: str, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    session.title = title
    db.commit()
    return {"message": "수정 완료"}