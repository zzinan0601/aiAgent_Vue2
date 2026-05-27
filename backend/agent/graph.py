from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import (
    analyze_node, tool_list_node, llm_node,
    tool_select_node, tool_call_node,
    generate_answer_node, evaluate_node, refine_node
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

    g.set_entry_point("analyze")

    g.add_conditional_edges(
        "analyze",
        lambda s: s["intent"],
        {
            "chat"     : "llm_chat",
            "tool"     : "tool_select",
            "tool_list": "tool_list",
        }
    )

    g.add_edge("tool_select",     "tool_call")
    g.add_edge("tool_call",       "generate_answer")
    g.add_edge("generate_answer", "evaluate")

    g.add_conditional_edges(
        "evaluate",
        lambda s: "end" if s["quality_ok"] else "refine",
        {"end": END, "refine": "refine"}
    )

    #g.add_edge("refine",    "tool_select")
    g.add_conditional_edges(
        "refine",
        lambda s: s["intent"],
        {
            "chat"     : "llm_chat",
            "tool"     : "tool_select",
        }
    )

    g.add_edge("llm_chat",  "evaluate")
    
    #g.add_edge("llm_chat",  END)
    g.add_edge("tool_list", END)

    return g.compile()

agent_graph = build_graph()
