import logging
from fastmcp import FastMCP
from modules.db_query import run_query

logger = logging.getLogger(__name__)

def register(mcp: FastMCP):

    @mcp.tool(
        description="""데이터베이스에 SQL을 직접 실행하여 데이터를 조회합니다.
정확한 수치, 집계, 특정 조건 조회에 사용합니다.

파라미터:
- sql (필수): 실행할 SELECT SQL 쿼리
- description: 이 쿼리가 무엇을 조회하는지 설명 (선택)

예시:
- 이번달 매출 합계 -> sql=SELECT SUM(amount) FROM sales WHERE ...
- 부서별 인원 수   -> sql=SELECT dept, COUNT(*) FROM employees GROUP BY dept"""
    )
    def db_query_tool(
        sql        : str,
        description: str = ""
    ) -> dict:
        logger.info("[db_query_tool] 시작 desc=" + description)
        logger.info("[db_query_tool] SQL: " + sql)

        if not sql.strip().upper().startswith("SELECT"):
            return {"status": "error", "message": "SELECT 쿼리만 허용됩니다."}

        rows = run_query(sql)
        logger.info("[db_query_tool] 조회 완료: " + str(len(rows)) + "건")

        return {
            "status"     : "success",
            "source"     : "db",
            "description": description,
            "sql"        : sql,
            "results"    : rows,
            "row_count"  : len(rows)
        }
