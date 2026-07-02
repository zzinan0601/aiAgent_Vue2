import logging
import httpx
from fastapi import APIRouter

from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", summary="Ollama 모델 목록 조회")
async def list_models():
    """Ollama 서버에서 사용 가능한 모델 목록을 반환합니다."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{settings.ollama_base_url}/api/tags")
            res.raise_for_status()
            data = res.json()
            logger.info("[models] Ollama 모델 목록 조회: " + str(len(data.get("models", []))) + "개")
            return data
    except Exception as e:
        logger.error("[models] Ollama 모델 목록 조회 실패: " + str(e))
        return {"models": []}
