import json
import logging
from fastmcp import Client
from config import settings

logger = logging.getLogger(__name__)

async def call_mcp_tool(tool_name: str, args: dict) -> dict:
    try:
        async with Client(settings.mcp_url) as client:
            logger.info("[MCP] 툴 호출: " + tool_name + " args=" + str(args))
            result = await client.call_tool(tool_name, args)

            if getattr(result, "is_error", False):
                return {"status": "error", "message": str(result)}

            if getattr(result, "structured_content", None):
                return result.structured_content

            content = getattr(result, "content", None)
            if content and isinstance(content, list) and hasattr(content[0], "text"):
                try:
                    parsed = json.loads(content[0].text)
                    logger.info("[MCP] 결과: status=" + str(parsed.get("status")))
                    return parsed
                except json.JSONDecodeError:
                    return {"status": "success", "result": content[0].text}

            return {"status": "error", "message": "빈 응답"}

    except Exception as e:
        logger.error("[MCP] 툴 호출 실패: " + str(e))
        return {"status": "error", "message": str(e)}


async def list_mcp_tools() -> list:
    try:
        async with Client(settings.mcp_url) as client:
            tools  = await client.list_tools()
            result = []
            for t in tools:
                params   = {}
                schema   = getattr(t, "inputSchema", {}) or {}
                props    = schema.get("properties", {})
                required = schema.get("required", [])
                for name, info in props.items():
                    params[name] = {
                        "type"       : info.get("type", "string"),
                        "required"   : name in required,
                        "default"    : info.get("default", ""),
                        "description": info.get("description", "")
                    }
                result.append({
                    "name"       : t.name,
                    "description": t.description or "",
                    "params"     : params
                })
            logger.info("[MCP] 툴 목록 로드: " + str([t["name"] for t in result]))
            return result
    except Exception as e:
        logger.error("[MCP] 툴 목록 조회 실패: " + str(e))
        return []
