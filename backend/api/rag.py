import os
import shutil
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from config import settings
from models.models import Document, Embedding, RagSetting, get_rag_settings
from schemas.rag import DocumentResponse, RagSettingsSchema
from rag.loader import load_file
from rag.chunker import split_text
from rag.embedder import embed_and_save

router = APIRouter()
logger = logging.getLogger(__name__)

import json
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks

@router.post("/upload", summary="파일 업로드")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: str = Form(None),
    db: Session = Depends(get_db)
):
    allowed = [".pdf", ".docx", ".txt"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="허용 파일: " + str(allowed))

    os.makedirs(settings.upload_dir, exist_ok=True)
    save_path = os.path.join(settings.upload_dir, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    user_meta = {}
    if metadata:
        try:
            user_meta = json.loads(metadata)
        except Exception:
            pass

    doc = Document(filename=file.filename, file_path=save_path, doc_metadata=user_meta)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(_run_embedding, doc.id, save_path)
    return {"doc_id": doc.id, "filename": file.filename, "status": "임베딩 시작됨"}

def _extract_metadata_via_llm(text: str) -> dict:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import SystemMessage, HumanMessage
    import re
    
    try:
        # 텍스트 앞부분(약 3000자)만 사용하여 요약/키워드 추출 (토큰 절약 및 속도)
        sample_text = text[:3000]
        
        prompt = """당신은 문서 메타데이터 추출기입니다.
다음 문서 내용을 분석하여 JSON 형식으로 메타데이터를 추출하세요.
반드시 마크다운 코드 블록(```json ... ```) 없이 순수 JSON 문자열만 반환해야 합니다.

필수 포함 항목:
- "category": 문서 종류 (예: "규정", "계약서", "회의록", "매뉴얼", "기타")
- "summary": 문서의 1~2줄 요약

문서 내용:
"""
        llm = ChatOllama(model=settings.llm_model, base_url=settings.ollama_base_url, temperature=0.1)
        response = llm.invoke([SystemMessage(content=prompt), HumanMessage(content=sample_text)])
        
        # JSON 파싱 시도
        res_text = response.content.strip()
        # ```json 제거
        res_text = re.sub(r"^```(?:json)?|```$", "", res_text, flags=re.MULTILINE).strip()
        
        return json.loads(res_text)
    except Exception as e:
        logger.warning(f"[메타데이터 자동 추출 실패] {e}")
        return {}

def _run_embedding(doc_id: int, file_path: str):
    from database import SessionLocal
    db = SessionLocal()
    try:
        logger.info("[임베딩 시작] doc_id=" + str(doc_id))
        text   = load_file(file_path)
        logger.info("[파싱 완료] 길이=" + str(len(text)))
        
        # 문서 모델 가져와서 현재 메타데이터 확인
        doc = db.query(Document).filter(Document.id == doc_id).first()
        user_meta = doc.doc_metadata or {}
        
        # LLM 자동 추출 진행
        logger.info("[메타데이터 추출 중...]")
        auto_meta = _extract_metadata_via_llm(text)
        logger.info(f"[메타데이터 추출 완료] {auto_meta}")
        
        # 사용자가 수동 입력한 값이 있으면 우선순위로 병합
        merged_meta = {**auto_meta, **user_meta}
        doc.doc_metadata = merged_meta
        db.commit()
        
        # DB에서 RAG 설정 조회
        rag_settings = get_rag_settings(db)
        chunks = split_text(
            text, 
            chunk_size=rag_settings.chunk_size, 
            chunk_overlap=rag_settings.chunk_overlap
        )
        logger.info(f"[청킹 완료] 수={len(chunks)} (크기={rag_settings.chunk_size}, 오버랩={rag_settings.chunk_overlap})")
        embed_and_save(db, doc_id, chunks, merged_meta)
        logger.info("[임베딩 완료] doc_id=" + str(doc_id))
    except Exception as e:
        import traceback
        logger.error("[임베딩 오류] " + str(e))
        logger.error(traceback.format_exc())
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = "error"
            db.commit()
    finally:
        db.close()

@router.get("/list", response_model=list[DocumentResponse], summary="문서 목록")
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.created_at.desc()).all()

@router.get("/status/{doc_id}", summary="임베딩 상태")
def embed_status(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    return {"doc_id": doc.id, "status": doc.status, "chunk_count": doc.chunk_count}

@router.get("/{doc_id}/chunks", summary="청크 내용 조회")
def get_chunks(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    chunks = db.query(Embedding).filter(Embedding.doc_id == doc_id).order_by(Embedding.chunk_index.asc()).all()
    return {
        "filename"   : doc.filename,
        "chunk_count": doc.chunk_count,
        "chunks"     : [{"index": c.chunk_index, "text": c.chunk_text} for c in chunks]
    }

@router.delete("/{doc_id}", summary="문서 삭제")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()
    return {"message": doc.filename + " 삭제 완료"}

# ── 기본지식 문서 토글 ──
@router.patch("/{doc_id}/knowledge", summary="기본지식 문서 설정/해제")
def toggle_knowledge(doc_id: int, is_knowledge: bool, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    if is_knowledge and doc.status != "done":
        raise HTTPException(status_code=400, detail="임베딩이 완료된 문서만 기본지식으로 설정할 수 있습니다")

    doc.is_knowledge = is_knowledge
    db.commit()
    return {
        "doc_id"      : doc.id,
        "filename"    : doc.filename,
        "is_knowledge": doc.is_knowledge
    }

# ── 기본지식 문서 목록 조회 ──
@router.get("/knowledge/list", summary="기본지식 문서 목록")
def list_knowledge_docs(db: Session = Depends(get_db)):
    docs = db.query(Document).filter(
        Document.is_knowledge == True,
        Document.status == "done"
    ).all()
    return [{"id": d.id, "filename": d.filename, "chunk_count": d.chunk_count} for d in docs]


# ── RAG 설정 조회 및 수정 ──
@router.get("/settings", response_model=RagSettingsSchema, summary="RAG 설정 조회")
def get_settings(db: Session = Depends(get_db)):
    return get_rag_settings(db)

@router.put("/settings", response_model=RagSettingsSchema, summary="RAG 설정 수정")
def update_settings(req: RagSettingsSchema, db: Session = Depends(get_db)):
    setting = get_rag_settings(db)
    setting.chunk_size     = req.chunk_size
    setting.chunk_overlap  = req.chunk_overlap
    setting.retrieve_top_k = req.retrieve_top_k
    setting.rerank_top_n   = req.rerank_top_n
    setting.dense_weight   = req.dense_weight
    setting.sparse_weight  = req.sparse_weight
    db.commit()
    db.refresh(setting)
    return setting

