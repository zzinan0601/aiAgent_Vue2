import logging
from fastmcp import FastMCP
from modules.vector_retrieve import vector_retrieve

logger = logging.getLogger(__name__)

def register(mcp: FastMCP):

    @mcp.tool(
        description="""사내 업로드 문서에서 관련 내용을 검색합니다.
RAG 벡터 검색 + 리랭크로 가장 관련성 높은 문서를 반환합니다.

파라미터:
- query (필수): 검색어 또는 질문
- top_k: 검색 결과 수 (기본값 5)

예시:
- 사내 휴가 규정 검색 -> query=연차 휴가 규정
- 계약서 내용 검색   -> query=계약 해지 조건"""
    )
    def document_query_tool(
        query: str,
        top_k: int = 5
    ) -> dict:
        logger.info("[document_query_tool] 시작 query=" + query[:50])

        results = vector_retrieve(query=query, top_k=top_k)
        logger.info("[document_query_tool] 검색 완료: " + str(len(results)) + "건")

        return {
            "status"   : "success",
            "source"   : "vector",
            "query"    : query,
            "results"  : results,
            "row_count": len(results)
        }
