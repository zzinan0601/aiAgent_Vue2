import json
import re
import logging
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
from agent.state import AgentState
from agent.mcp_client import call_mcp_tool, list_mcp_tools
from config import settings

logger = logging.getLogger(__name__)
llm    = ChatOllama(base_url=settings.ollama_base_url, model=settings.llm_model)

# ── 툴 목록 캐시 ──────────────────────────────
_tool_cache: list = []

# ── 최종 프롬프트 컨텍스트 캐시 ───────────────
_last_context_cache: dict = {}

def set_last_context(session_id: str, messages: list):
    if session_id:
        _last_context_cache[session_id] = list(messages)

def get_last_context(session_id: str) -> list:
    return _last_context_cache.get(session_id, [])

def get_tool_cache() -> list:
    return _tool_cache

def get_tool_names() -> list:
    return [t["name"] for t in _tool_cache]

def get_tool_map() -> dict:
    return {t["name"]: t for t in _tool_cache}

async def load_tools_from_mcp():
    global _tool_cache
    import asyncio
    for attempt in range(5):
        tools = await list_mcp_tools()
        if tools:
            _tool_cache = tools
            logger.info("[tools] MCP 툴 로드 완료: " + str(get_tool_names()))
            return
        logger.warning("[tools] 툴 로드 실패 (" + str(attempt + 1) + "/5) 3초 후 재시도...")
        await asyncio.sleep(3)
    logger.error("[tools] MCP 툴 로드 최종 실패")


# ── 노드 1: 질문 분석 ──
def analyze_node(state: AgentState) -> dict:
    mode     = state.get("mode", "auto")
    last_msg = state["messages"][-1].content

    logger.info("=" * 60)
    logger.info("[analyze] 질문: " + last_msg)
    logger.info("[analyze] mode: " + mode)

    if mode == "chat":
        return {"intent": "chat"}
    if mode == "tool":
        return {"intent": "tool"}

    at_match = re.match(r"@(\w+)\s*(.*)", last_msg.strip(), re.DOTALL)
    if at_match:
        tool_name = at_match.group(1)
        if tool_name in get_tool_names():
            logger.info("[analyze] @ 툴 지정: " + tool_name)
            return {"intent": "tool", "tool_name": tool_name}

    for name in get_tool_names():
        if name in last_msg:
            logger.info("[analyze] 툴 이름 감지: " + name)
            return {"intent": "tool", "tool_name": name}

    if "툴 목록" in last_msg or "tool list" in last_msg.lower():
        return {"intent": "tool_list"}

    prompt = (
        "사용자 질문을 분석하세요.\n"
        "툴이 필요하면 'tool', 일반 대화면 'chat'으로만 답하세요.\n"
        "툴 목록: " + str(get_tool_names()) + "\n"
        "질문: " + last_msg + "\n"
        "판단:"
    )
    res    = llm.invoke([HumanMessage(content=prompt)])
    intent = "tool" if "tool" in res.content.lower() else "chat"
    logger.info("[analyze] LLM 응답: '" + res.content.strip() + "' → intent=" + intent)
    return {"intent": intent}


# ── 노드 2: 툴 목록 응답 ──
def tool_list_node(state: AgentState) -> dict:
    lines = ["사용 가능한 툴 목록:\n"]
    for t in get_tool_cache():
        first_line = t["description"].splitlines()[0]
        lines.append("- **" + t["name"] + "**: " + first_line)
    return {"final_answer": "\n".join(lines)}


# ── 노드 3: 일반 LLM 대화 (스트리밍) ──
def llm_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1].content
    
    session_id = state.get("session_id")
    temp = 0.7
    if session_id:
        from database import SessionLocal
        from models.models import Session as SessionModel
        db = SessionLocal()
        try:
            sess = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if sess and sess.temperature is not None:
                temp = sess.temperature
        except Exception as e:
            logger.warning(f"[llm_node] Error fetching temperature: {e}")
        finally:
            db.close()

    logger.info(f"[llm_chat] 시작: {last_msg[:80]} | 온도: {temp}")
    
    # 최종 컨텍스트 캐싱
    set_last_context(session_id, state["messages"])
    
    local_llm = ChatOllama(base_url=settings.ollama_base_url, model=settings.llm_model, temperature=temp)
    full_content = ""
    for chunk in local_llm.stream(state["messages"]):
        if chunk.content:
            full_content += chunk.content
    logger.info("[llm_chat] 응답 " + str(len(full_content)) + "자")
    return {"final_answer": full_content}


# ── 노드 4: 툴 선택 & 인자 추출 ──
def tool_select_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1].content
    tool_map = get_tool_map()
    pre_selected_tool = state.get("tool_name")

    if pre_selected_tool:
        logger.info("[tool_select] 툴 지정됨: " + pre_selected_tool)
        if pre_selected_tool not in tool_map:
            logger.warning("[tool_select] 지정된 툴이 tool_map에 없음: " + pre_selected_tool)
            return {"tool_args": {}}
            
        tool_info = tool_map[pre_selected_tool]
        tool_schema = json.dumps(tool_info, ensure_ascii=False, indent=2)
        prompt = (
            f"사용자가 툴 '{pre_selected_tool}'을 사용하기로 지정했습니다.\n"
            f"아래 [툴 스키마]를 참고하여 사용자 질문에서 해당 툴에 필요한 인자(arguments)만 추출하세요.\n\n"
            f"[툴 스키마]\n{tool_schema}\n\n"
            f"[중요 규칙]\n"
            f"- 스키마에 정의된 파라미터만 사용하세요\n"
            f"- required=true 파라미터는 반드시 포함하세요\n"
            f"- 정의되지 않은 파라미터는 절대 추가하지 마세요\n\n"
            f"[사용자 질문]\n{last_msg}\n\n"
            f"[반환 형식 - JSON만 반환]\n"
            f'{{"args": {{파라미터만}}}}'
        )
    else:
        tool_schema = json.dumps(get_tool_cache(), ensure_ascii=False, indent=2)
        prompt = (
            "사용자 질문에 맞는 툴과 인자를 선택하세요.\n\n"
            "[툴 목록 및 파라미터 스키마]\n" + tool_schema + "\n\n"
            "[중요 규칙]\n"
            "- 스키마에 정의된 파라미터만 사용하세요\n"
            "- required=true 파라미터는 반드시 포함하세요\n"
            "- 정의되지 않은 파라미터는 절대 추가하지 마세요\n\n"
            "[사용자 질문]\n" + last_msg + "\n\n"
            "[반환 형식 - JSON만 반환]\n"
            '{"tool_name": "툴이름", "args": {파라미터만}}'
        )

    logger.info("[tool_select] LLM 툴 선택/인자 추출 요청 중...")
    res = llm.invoke([HumanMessage(content=prompt)])
    logger.info("[tool_select] LLM 원본 응답:\n" + res.content)

    try:
        raw = res.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1].replace("json", "").strip()
        parsed    = json.loads(raw)
        
        tool_name = pre_selected_tool if pre_selected_tool else parsed.get("tool_name", "")
        
        # 1. Extract args with fallback keys
        tool_args = {}
        for key in ["args", "tool_args", "arguments"]:
            if key in parsed and isinstance(parsed[key], dict):
                tool_args = dict(parsed[key])
                break
        
        # 2. Extract valid parameters from root level as fallback
        if tool_name in tool_map:
            valid_keys = set(tool_map[tool_name]["params"].keys())
            for k in valid_keys:
                if k in parsed and k not in tool_args:
                    tool_args[k] = parsed[k]
            
            removed    = {k: v for k, v in tool_args.items() if k not in valid_keys}
            tool_args  = {k: v for k, v in tool_args.items() if k in valid_keys}
            if removed:
                logger.warning("[tool_select] 잘못된 파라미터 제거: " + str(removed))

        logger.info("[tool_select] 최종 선택: " + tool_name + " args=" + str(tool_args))
        return {"tool_name": tool_name, "tool_args": tool_args}

    except Exception as e:
        logger.error("[tool_select] 파싱 실패: " + str(e))
        logger.error("[tool_select] LLM 원문: " + res.content)
        return {"tool_name": pre_selected_tool or "", "tool_args": {}}


# ── 노드 5: FastMCP 툴 호출 ──
async def tool_call_node(state: AgentState) -> dict:
    tool_name = state.get("tool_name", "")
    tool_args = state.get("tool_args", {})

    logger.info("[tool_call] 시작: " + tool_name + " args=" + json.dumps(tool_args, ensure_ascii=False))

    if not tool_name:
        return {"tool_result": {"status": "error", "message": "툴을 선택하지 못했습니다."}}

    result = await call_mcp_tool(tool_name, tool_args)

    logger.info("[tool_call] 완료: status=" + str(result.get("status")))
    if result.get("status") == "error":
        logger.error("[tool_call] 오류: " + str(result.get("message")))
    else:
        if "results" in result:
            logger.info("[tool_call] 검색 결과 " + str(len(result["results"])) + "건")
            for i, r in enumerate(result["results"][:2]):
                logger.info("  [결과" + str(i) + "] " + str(r)[:150])
        if "chart_url" in result:
            logger.info("[tool_call] 차트: " + result["chart_url"])
        if "row_count" in result:
            logger.info("[tool_call] row_count=" + str(result["row_count"]))

    return {"tool_result": result}


# ── 노드 6: 응답 생성 (툴별 전용 프롬프트 + 스트리밍) ──
def generate_answer_node(state: AgentState) -> dict:
    tool_result = state.get("tool_result") or {}
    tool_name   = state.get("tool_name")   or ""
    last_q      = state["messages"][-1].content

    logger.info("[generate] 시작 tool=" + tool_name + " result_keys=" + str(list(tool_result.keys())))

    chart_url = tool_result.get("chart_url", "")
    chart_md  = ""
    if chart_url:
        chart_md = "\n\n" + "![차트](" + chart_url + ")"

    status = tool_result.get("status", "")

    if tool_name == "report_tool" and status == "success":
        prompt = _build_report_prompt(last_q, tool_result)

    elif tool_name == "document_query_tool" and status == "success":
        prompt = _build_document_query_prompt(last_q, tool_result)

    elif tool_name == "db_query_tool" and status == "success":
        prompt = _build_db_query_prompt(last_q, tool_result)

    else:
        prompt = (
            "사용자 질문에 대한 실행 결과입니다.\n"
            "결과를 한국어로 친절하게 설명해주세요.\n"
            "질문: " + last_q + "\n"
            "결과: " + json.dumps(tool_result, ensure_ascii=False) + "\n"
            "답변:"
        )

    session_id = state.get("session_id")
    temp = 0.7
    if session_id:
        from database import SessionLocal
        from models.models import Session as SessionModel
        db = SessionLocal()
        try:
            sess = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if sess and sess.temperature is not None:
                temp = sess.temperature
        except Exception as e:
            logger.warning(f"[generate_answer_node] Error fetching temperature: {e}")
        finally:
            db.close()

    logger.info(f"[generate] 시작 tool={tool_name} | 온도={temp}")

    # 기존 대화 이력 복사 (페르소나 및 Few-shot 예시 유지 목적)
    messages_to_send = list(state["messages"])
    if messages_to_send:
        # 마지막 사용자의 최신 질문 메시지를 툴 결과 프롬프트 메시지로 치환
        messages_to_send[-1] = HumanMessage(content=prompt)
    else:
        messages_to_send = [HumanMessage(content=prompt)]

    # 최종 컨텍스트 캐싱
    set_last_context(session_id, messages_to_send)

    # local_llm.stream 으로 토큰 단위 스트리밍
    local_llm = ChatOllama(base_url=settings.ollama_base_url, model=settings.llm_model, temperature=temp)
    full_content = ""
    for chunk in local_llm.stream(messages_to_send):
        if chunk.content:
            full_content += chunk.content

    logger.info("[generate] 답변 " + str(len(full_content)) + "자: " + full_content[:200])
    return {"final_answer": full_content + chart_md}


# ── 툴별 프롬프트 빌더 ──────────────────────────────────────────

def _build_report_prompt(question: str, result: dict) -> str:
    data       = result.get("data", [])
    period     = result.get("period", "")
    query_type = result.get("query_type", "")
    row_count  = result.get("row_count", 0)
    return (
        "다음은 " + period + " " + query_type + " 데이터입니다. 한국어로 리포트를 작성해주세요.\n\n"
        "[분석 요청]\n" + question + "\n\n"
        "[데이터 (" + str(row_count) + "건)]\n"
        + json.dumps(data, ensure_ascii=False, indent=2) + "\n\n"
        "[작성 규칙]\n"
        "1. 데이터를 마크다운 표(|컬럼|)로 정리하세요\n"
        "2. 숫자는 천단위 콤마(,)를 붙이세요\n"
        "3. 최고값 / 최저값 / 평균값을 계산하여 포함하세요\n"
        "4. 전체 트렌드를 2~3줄로 요약하세요\n"
        "5. 주목할 인사이트나 이상값이 있으면 언급하세요\n\n"
        "리포트:"
    )


def _build_document_query_prompt(question: str, result: dict) -> str:
    results = result.get("results", [])
    if not results:
        return (
            "질문: " + question + "\n"
            "결과: 관련 문서를 찾을 수 없습니다.\n"
            "검색된 문서가 없다고 안내해주세요.\n"
            "답변:"
        )
    context_parts = []
    for i, r in enumerate(results, 1):
        filename = r.get("filename", "알 수 없음")
        text     = r.get("chunk_text", r.get("text", ""))
        score    = float(r.get("score", 0))
        summary  = r.get("summary", "")
        last_mod = r.get("last_modified_date", "")
        
        meta_str = f"출처: {filename} (유사도: {round(score, 2)})"
        if last_mod:
            date_only = last_mod.split("T")[0]
            meta_str += f", 최종수정일: {date_only}"
            
        chunk_info = f"[{i}. {meta_str}]\n"
        if summary:
            chunk_info += f"[문서 요약]\n{summary}\n\n"
        chunk_info += f"[본문 내용]\n{text}"
        
        context_parts.append(chunk_info)
    context = "\n\n".join(context_parts)
    return (
        "다음은 사내 문서 검색 결과입니다. 검색 내용을 바탕으로 질문에 답해주세요.\n\n"
        "[질문]\n" + question + "\n\n"
        "[검색된 문서 내용]\n" + context + "\n\n"
        "[답변 규칙]\n"
        "- 검색 결과에 있는 내용만 사용하세요\n"
        "- 출처파일과 파일의 최종수정일을 년월일형식으로 언급하세요\n"
        "- 검색 결과에 없는 내용은 문서에서 찾을 수 없다고 답하세요\n\n"
        "답변:"
    )


def _build_db_query_prompt(question: str, result: dict) -> str:
    results     = result.get("results", [])
    row_count   = result.get("row_count", len(results))
    description = result.get("description", "")
    if not results:
        return (
            "질문: " + question + "\n"
            "조회 결과: 데이터가 없습니다.\n"
            "데이터가 없다고 안내해주세요.\n"
            "답변:"
        )
    return (
        "다음은 DB 조회 결과입니다. 결과를 한국어로 설명해주세요.\n\n"
        "[질문]\n" + question + "\n\n"
        + ("[쿼리 설명]\n" + description + "\n\n" if description else "")
        + "[조회 결과 (" + str(row_count) + "건)]\n"
        + json.dumps(results, ensure_ascii=False, indent=2) + "\n\n"
        "[작성 규칙]\n"
        "- 데이터가 여러 행이면 마크다운 표로 정리하세요\n"
        "- 숫자는 천단위 콤마(,)를 붙이세요\n"
        "- 핵심 수치를 요약해주세요\n\n"
        "답변:"
    )


# ── 노드 7: 품질 평가 ──
def evaluate_node(state: AgentState) -> dict:
    retry_count = state.get("retry_count", 0)
    tool_result = state.get("tool_result", {})
    answer      = state.get("final_answer", "")

    logger.info("[evaluate] retry=" + str(retry_count) + " 답변길이=" + str(len(answer)))

    if retry_count >= 1:
        return {"quality_ok": True}
    # if tool_result.get("status") == "success":
    #     return {"quality_ok": True}
    # if len(answer) > 100:
    #     return {"quality_ok": True}

    prompt = (
        "답변이 질문에 충분히 답하고 있나요? 'yes' 또는 'no'만 답하세요.\n"
        "질문: " + state["messages"][-1].content + "\n"
        "답변: " + answer[:300] + "\n"
        "평가:"
    )
    res   = llm.invoke([HumanMessage(content=prompt)])
    is_ok = "no" not in res.content.lower()
    
    logger.info("[evaluate] LLM: '" + res.content.strip() + "' → " + str(is_ok))
    return {"quality_ok": is_ok, "retry_count": retry_count + 1}


# ── 노드 8: 질문 보완 ──
def refine_node(state: AgentState) -> dict:
    last_q = state["messages"][-1].content
    answer = state.get("final_answer", "")
    logger.info("[refine] 원래질문: " + last_q)

    prompt = (
        "답변이 부족합니다. 질문을 보완해주세요. 보완된 질문만 반환하세요.\n"
        "원래 질문: " + last_q + "\n"
        "부족한 답변: " + answer + "\n"
        "보완된 질문:"
    )
    res = llm.invoke([HumanMessage(content=prompt)])
    logger.info("[refine] 보완: " + res.content.strip())
    return {
        "messages": [
            AIMessage(content=answer),
            HumanMessage(content=res.content.strip())
        ]
    }


# ── 노드 9: 에러 핸들러 ──
def error_handler_node(state: AgentState) -> dict:
    tool_result = state.get("tool_result", {})
    error       = state.get("error", "")

    if tool_result.get("status") == "error":
        error_msg = tool_result.get("message", "알 수 없는 오류가 발생했습니다.")
    elif error:
        error_msg = error
    else:
        error_msg = "처리 중 오류가 발생했습니다."

    logger.error("[error_handler] " + error_msg)
    return {"final_answer": "⚠️ 오류가 발생했습니다: " + error_msg + "\n\n다시 시도해 주세요."}
