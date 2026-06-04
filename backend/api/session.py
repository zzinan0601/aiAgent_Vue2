import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.models import Session as SessionModel, Message, Document, Embedding
from schemas.chat import SessionResponse, CreateSessionRequest, MessageResponse, UpdateSessionRequest

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
        system_prompt = system_prompt,
        use_knowledge = req.use_knowledge,
        temperature   = req.temperature if req.temperature is not None else 0.7
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agent.nodes import get_last_context
import json

def _load_session_history_fallback(db: Session, session: SessionModel) -> list:
    msgs = db.query(Message).filter(
        Message.session_id == session.id
    ).order_by(Message.created_at.asc()).all()

    history = []
    
    if session.system_prompt:
        history.append(SystemMessage(content=session.system_prompt))
        
    if session.few_shots:
        try:
            few_shots_list = json.loads(session.few_shots)
            if isinstance(few_shots_list, list):
                for fs in few_shots_list:
                    if fs.get("user") and fs.get("assistant"):
                        history.append(HumanMessage(content=fs["user"]))
                        history.append(AIMessage(content=fs["assistant"]))
        except Exception:
            pass
            
    for m in msgs:
        if m.role == "user":
            history.append(HumanMessage(content=m.content))
        else:
            history.append(AIMessage(content=m.content))
            
    return history

@router.get("/{session_id}/context", summary="현재 컨텍스트 전체 조회")
def get_session_context(session_id: str, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    cached_messages = get_last_context(session_id)

    if not cached_messages:
        cached_messages = _load_session_history_fallback(db, session)

    serialized = []
    for msg in cached_messages:
        role = "system" if msg.__class__.__name__ == "SystemMessage" else \
               "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
        serialized.append({
            "role": role,
            "content": msg.content
        })

    return {
        "session_id": session_id,
        "use_knowledge": session.use_knowledge,
        "context": serialized
    }


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


@router.patch("/{session_id}", response_model=SessionResponse, summary="세션 설정 수정")
def update_session(session_id: str, req: UpdateSessionRequest, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    
    if req.title is not None:
        session.title = req.title
    if req.system_prompt is not None:
        session.system_prompt = req.system_prompt
    if req.few_shots is not None:
        session.few_shots = req.few_shots
    if req.use_knowledge is not None:
        session.use_knowledge = req.use_knowledge
    if req.temperature is not None:
        session.temperature = req.temperature
        
    db.commit()
    db.refresh(session)
    return session