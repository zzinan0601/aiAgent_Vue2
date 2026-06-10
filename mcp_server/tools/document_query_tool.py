import logging
from fastmcp import FastMCP
from modules.vector_retrieve import vector_retrieve

logger = logging.getLogger(__name__)

from typing import Optional, Union
import json

def register(mcp: FastMCP):

    @mcp.tool(
        description="""사내 업로드 문서에서 관련 내용을 검색합니다.
RAG 벡터 검색 + 리랭크로 가장 관련성 높은 문서를 반환합니다.

파라미터:
- query (필수): 검색어 또는 질문
- filters (선택): 메타데이터 필터링 조건. 예: {"category": "규정"}

예시:
- 사내 휴가 규정 검색 -> query="연차 휴가 규정"
- 계약서 내용 검색 -> query="계약 해지 조건", filters={"category": "계약서"}

주의사항:
- 검색 결과에는 각 청크별 원본 문서의 요약(summary)과 최종수정일(last_modified_date)이 포함됩니다.
- 답변을 생성할 때 summary를 참고하여 전체 문맥을 파악하세요.
- 답변의 출처를 표기할 때 문서 이름과 함께 최종수정일을 반드시 명시해 주세요."""
    )
    def document_query_tool(
        query: str,
        filters: Union[dict, str, None] = None
    ) -> dict:
        # LLM이 JSON 문자열로 전달할 경우 대비 파싱 로직 추가
        if isinstance(filters, str):
            try:
                filters = json.loads(filters)
            except Exception:
                logger.warning("[document_query_tool] filters JSON 파싱 실패: " + filters)
                filters = None

        logger.info("[document_query_tool] 시작 query=" + query[:50] + " filters=" + str(filters))

        results = vector_retrieve(query=query, filters=filters)
        logger.info("[document_query_tool] 검색 완료: " + str(len(results)) + "건")

        return {
            "status"   : "success",
            "source"   : "vector",
            "query"    : query,
            "filters"  : filters,
            "results"  : results,
            "row_count": len(results)
        }
