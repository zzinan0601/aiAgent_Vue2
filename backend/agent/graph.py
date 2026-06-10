from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import (
    analyze_node, tool_list_node, llm_node,
    tool_select_node, tool_call_node,
    generate_answer_node, evaluate_node, refine_node,
    error_handler_node
)

def build_graph():
    g = StateGraph(AgentState)

    g.add_node("analyze",         analyze_node)
    g.add_node("tool_list",       tool_list_node)
    g.add_node("llm_chat",        llm_node)
    g.add_node("tool_select",     tool_select_node)
    g.add_node("tool_call",       tool_call_node)
    g.add_node("generate_answer", generate_answer_node)
    g.add_node("evaluate",        evaluate_node)
    g.add_node("refine",          refine_node)
    g.add_node("error_handler",   error_handler_node)

    g.set_entry_point("analyze")

    # ── 1. analyze: 예상치 못한 intent 값은 chat으로 fallback ──
    g.add_conditional_edges(
        "analyze",
        lambda s: s["intent"] if s["intent"] in ("chat", "tool", "tool_list") else "chat",
        {
            "chat"     : "llm_chat",
            "tool"     : "tool_select",
            "tool_list": "tool_list",
        }
    )

    # ── 2. tool_select: 툴 선택 실패 시 llm_chat으로 fallback ──
    g.add_conditional_edges(
        "tool_select",
        lambda s: "tool_call" if s.get("tool_name") else "llm_chat",
        {"tool_call": "tool_call", "llm_chat": "llm_chat"}
    )

    # ── 3. tool_call: 에러 시 error_handler로 분기 ──
    g.add_conditional_edges(
        "tool_call",
        lambda s: "generate_answer" if s.get("tool_result", {}).get("status") == "success" else "error_handler",
        {"generate_answer": "generate_answer", "error_handler": "error_handler"}
    )

    g.add_edge("generate_answer", "evaluate")

    # ── 4. evaluate: 그래프 레벨 retry guard 포함 ──
    g.add_conditional_edges(
        "evaluate",
        lambda s: "end" if s["quality_ok"] or s.get("retry_count", 0) >= 1 else "refine",
        {"end": END, "refine": "refine"}
    )

    # ── 5. refine → analyze: intent 재분석 ──
    g.add_edge("refine", "analyze")

    g.add_edge("llm_chat",      "evaluate")
    g.add_edge("tool_list",     END)
    g.add_edge("error_handler", END)

    return g.compile()

agent_graph = build_graph()
