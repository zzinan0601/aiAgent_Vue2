import logging
from config import settings

logger    = logging.getLogger(__name__)
_embedder = None
_reranker = None

def get_embedder():
    global _embedder
    if _embedder is None:
        # 서버 시작 시 임포트 X → 실제 호출될 때만 임포트
        from FlagEmbedding import BGEM3FlagModel
        path = settings.embed_model_abs_path
        logger.info("[모델 로드] BGE-M3: " + path)
        _embedder = BGEM3FlagModel(path, use_fp16=settings.use_fp16)
    return _embedder

def get_reranker():
    global _reranker
    if _reranker is None:
        from FlagEmbedding import FlagReranker
        path = settings.reranker_model_abs_path
        logger.info("[모델 로드] BGE-Reranker: " + path)
        _reranker = FlagReranker(path, use_fp16=settings.use_fp16)
    return _reranker