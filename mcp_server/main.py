from logger import setup_logging
setup_logging()

import logging
from fastmcp import FastMCP
from config import mcp_settings

logger = logging.getLogger(__name__)
mcp    = FastMCP(name="AI Agent MCP Server")

from tools.report_tool         import register as reg_report
from tools.document_query_tool import register as reg_document
from tools.db_query_tool       import register as reg_db

reg_report(mcp)
reg_document(mcp)
reg_db(mcp)

if __name__ == "__main__":
    logger.info("FastMCP SSE 시작 포트=" + str(mcp_settings.mcp_port))
    mcp.run(transport="sse", host="0.0.0.0", port=mcp_settings.mcp_port)
