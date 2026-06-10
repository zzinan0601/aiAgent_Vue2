from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages    : Annotated[list, add_messages]
    mode        : str
    intent      : str
    tool_name   : str
    tool_args   : dict
    tool_result : dict
    final_answer: str
    quality_ok  : bool
    retry_count : int
    session_id  : str
    error       : str
