import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage
from database import get_db
from schemas.chat import ChatRequest
from models.models import Session as SessionModel, Message
from agent.graph import agent_graph

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", summary="채팅 (SSE 스트리밍)")
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    logger.info("[chat] session=" + req.session_id + " mode=" + req.mode + " model=" + req.model + " msg=" + req.message[:50])
    history = _load_history(db, req.session_id)
    history.append(HumanMessage(content=req.message))
    return StreamingResponse(
        _stream_agent(db, req.session_id, req.message, history, req.mode, req.model),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

async def _stream_agent(db, session_id, user_msg, history, mode, model=""):
    try:
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        use_knowledge = session.use_knowledge if session else False

        initial_state = {
            "messages"   : history,
            "session_id" : session_id,
            "mode"       : mode,
            "model"      : model,
            "use_knowledge": use_knowledge,
            "retry_count": 0,
            "quality_ok" : False,
        }

        final_answer     = ""
        current_tool     = ""
        generation_count = 0   # 생성 횟수 추적

        async for event in agent_graph.astream_events(initial_state, version="v2"):
            kind      = event["event"]
            node_name = event.get("metadata", {}).get("langgraph_node", "")

            # LLM 토큰 스트리밍
            if kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if chunk and chunk.content:
                    if node_name in ("generate_answer", "llm_chat"):
                        final_answer += chunk.content
                        yield (
                            "data: " +
                            json.dumps({"type": "token", "content": chunk.content}, ensure_ascii=False) +
                            "\n\n"
                        )

            elif kind == "on_chain_start" and node_name:

                # ── 재생성 시작 감지 → 기존 답변 초기화 ──
                if node_name in ("generate_answer", "llm_chat"):
                    if generation_count > 0:
                        # 두 번째 생성부터는 기존 답변 지우기
                        final_answer = ""
                        yield (
                            "data: " +
                            json.dumps({"type": "clear"}) +
                            "\n\n"
                        )
                        logger.info("[chat] 재생성 시작 - 기존 답변 초기화")
                    generation_count += 1

                # 상태 메시지
                status = _get_status_msg(node_name, {}, current_tool)
                if status:
                    yield (
                        "data: " +
                        json.dumps({"type": "status", "content": status}, ensure_ascii=False) +
                        "\n\n"
                    )

            elif kind == "on_chain_end" and node_name:
                output = event["data"].get("output", {})
                if isinstance(output, dict):
                    if output.get("tool_name"):
                        current_tool = output["tool_name"]
                    if output.get("final_answer") and len(output["final_answer"]) > len(final_answer):
                        remaining = output["final_answer"][len(final_answer):]
                        final_answer = output["final_answer"]
                        yield (
                            "data: " +
                            json.dumps({"type": "token", "content": remaining}, ensure_ascii=False) +
                            "\n\n"
                        )

        _save_message(db, session_id, "user",      user_msg)
        _save_message(db, session_id, "assistant", final_answer)
        _auto_set_title(db, session_id, user_msg)
        logger.info("[chat] 완료 session=" + session_id)

        yield "data: " + json.dumps({"type": "done"}) + "\n\n"

    except Exception as e:
        import traceback
        logger.error("[chat] 오류: " + str(e) + "\n" + traceback.format_exc())
        yield (
            "data: " +
            json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False) +
            "\n\n"
        )

def _get_status_msg(node_name: str, node_output: dict, current_tool: str) -> str:
    if node_name == "analyze":
        return "🔍 질문 분석 중..."
    if node_name == "tool_select":
        tool_labels = {
            "report_tool"         : "📊 리포트 생성 툴",
            "document_query_tool" : "🔎 문서 검색 툴",
            "db_query_tool"       : "🗄️ DB 조회 툴",
            "chart_tool"          : "📈 차트 생성 툴",
            "email_tool"          : "📧 이메일 발송 툴",
        }
        label = tool_labels.get(current_tool, current_tool)
        return "🛠️ " + label + " 선택 중..."
    if node_name == "tool_call":
        tool_steps = {
            "document_query_tool": "🔢 문서 임베딩 및 벡터 검색 중...",
            "db_query_tool"      : "🗄️ DB 쿼리 실행 중...",
            "report_tool"        : "🗄️ 데이터 조회 및 차트 생성 중...",
            "chart_tool"         : "📊 차트 이미지 생성 중...",
            "email_tool"         : "📧 이메일 발송 중...",
        }
        return tool_steps.get(current_tool, "⚙️ 툴 실행 중...")
    if node_name == "generate_answer":
        return "✍️ 답변 생성 중..."
    if node_name == "evaluate":
        return "📊 품질 검토 중..."
    if node_name == "refine":
        return "🔄 답변 보완 중..."
    return ""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

def _load_history(db: Session, session_id: str) -> list:
    # 세션 정보 로드
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    msgs    = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at.asc()).all()

    history = []

    # system_prompt 있으면 맨 앞에 추가
    if session and session.system_prompt:
        history.append(SystemMessage(content=session.system_prompt))
        logger.info("[chat] system_prompt 주입: " + str(len(session.system_prompt)) + "자")

    # few_shots 있으면 system_prompt 바로 뒤에 주입
    if session and session.few_shots:
        try:
            few_shots_list = json.loads(session.few_shots)
            if isinstance(few_shots_list, list):
                for fs in few_shots_list:
                    if fs.get("user") and fs.get("assistant"):
                        history.append(HumanMessage(content=fs["user"]))
                        history.append(AIMessage(content=fs["assistant"]))
                logger.info("[chat] few_shots 주입: " + str(len(few_shots_list)) + "쌍")
        except Exception as e:
            logger.error("[chat] few_shots 파싱 실패: " + str(e))

    for m in msgs:
        if m.role == "user":
            history.append(HumanMessage(content=m.content))
        else:
            history.append(AIMessage(content=m.content))

    return history

def _save_message(db: Session, session_id: str, role: str, content: str):
    db.add(Message(session_id=session_id, role=role, content=content))
    db.commit()

def _auto_set_title(db: Session, session_id: str, first_msg: str):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if session and session.title in ["새 채팅", None]:
        session.title = first_msg[:30]
        db.commit()
