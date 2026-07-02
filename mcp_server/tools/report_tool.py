import logging
from fastmcp import FastMCP
from modules.db_query       import run_query
from modules.chart_generate import generate_bar_chart, generate_line_chart

logger = logging.getLogger(__name__)

def register(mcp: FastMCP):

    @mcp.tool(
        description="""월별/일별 데이터를 조회하여 차트를 생성합니다.
리포트 텍스트 생성은 에이전트가 담당합니다.

파라미터:
- query_type (필수): monthly_sales(월별매출) / daily_sales(일별매출)
- period (필수): 연도(2024) 또는 연월(2024-01)
- chart_type: bar(막대차트, 기본값) / line(꺾은선차트)

예시:
- 2024년 월별 매출 -> query_type=monthly_sales, period=2024
- 2024년 1월 일별  -> query_type=daily_sales, period=2024-01"""
    )
    def report_tool(
        query_type: str,
        period    : str,
        chart_type: str = "bar",
    ) -> dict:
        logger.info("[report_tool] 시작 query_type=" + query_type + " period=" + period)

        sql, params = _build_sql(query_type, period)
        rows = run_query(sql, params)
        logger.info("[report_tool] 데이터 조회 완료: " + str(len(rows)) + "건")

        if not rows:
            return {"status": "error", "message": "해당 기간의 데이터가 없습니다."}

        labels = [str(r.get("label", i)) for i, r in enumerate(rows)]
        values = [float(r.get("value", r.get("amount", 0))) for r in rows]

        fn         = generate_line_chart if chart_type == "line" else generate_bar_chart
        chart_info = fn(labels, values, title=period + " " + query_type)
        logger.info("[report_tool] 차트 생성 완료 (Base64 URL 생성됨)")

        return {
            "status"      : "success",
            "query_type"  : query_type,
            "period"      : period,
            "data"        : rows,
            "row_count"   : len(rows),
            "chart_url"   : chart_info["url"],
            "chart_base64": chart_info.get("base64", chart_info["url"]),
            "chart_path"  : chart_info["path"],
            "labels"      : labels,
            "values"      : values,
        }


def _build_sql(query_type: str, period: str):
    if query_type == "monthly_sales":
        return (
            "SELECT TO_CHAR(sale_date,'MM') AS label, SUM(amount) AS value "
            "FROM sales WHERE EXTRACT(YEAR FROM sale_date)=%s "
            "GROUP BY label ORDER BY label",
            (period,)
        )
    elif query_type == "daily_sales":
        return (
            "SELECT TO_CHAR(sale_date,'DD') AS label, SUM(amount) AS value "
            "FROM sales WHERE TO_CHAR(sale_date,'YYYY-MM')=%s "
            "GROUP BY label ORDER BY label",
            (period,)
        )
    else:
        return ("SELECT 'N/A' AS label, COUNT(*) AS value FROM sales", ())
