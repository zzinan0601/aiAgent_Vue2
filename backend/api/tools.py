import logging
from fastapi import APIRouter
from agent.nodes import get_tool_cache
from agent.mcp_client import list_mcp_tools

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", summary="툴 목록 조회 (프론트엔드 @ 자동완성용)")
async def get_tools():
    tools = get_tool_cache()
    if not tools:
        logger.info("[api/tools] 캐시 없음 → MCP 재조회")
        tools = await list_mcp_tools()
    return [
        {
            "name"            : t["name"],
            "description"     : t["description"].splitlines()[0],
            "full_description": t["description"],
        }
        for t in tools
    ]
