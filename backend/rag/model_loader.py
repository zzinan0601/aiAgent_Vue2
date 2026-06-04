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
        try:
            from transformers.tokenization_utils_base import PreTrainedTokenizerBase, BatchEncoding
            
            def prepare_for_model_patch(
                self,
                ids,
                pair_ids=None,
                max_length=None,
                padding=False,
                truncation=False,
                stride=0,
                pad_to_multiple_of=None,
                return_tensors=None,
                prepend_batch_axis=False,
                **kwargs
            ) -> BatchEncoding:
                bos = self.bos_token_id if self.bos_token_id is not None else 0
                eos = self.eos_token_id if self.eos_token_id is not None else 2
                
                # Truncation
                if max_length is not None:
                    num_special = 4 if pair_ids is not None else 2
                    available_len = max_length - num_special
                    if pair_ids is not None:
                        if len(ids) + len(pair_ids) > available_len:
                            pair_len = max(0, available_len - len(ids))
                            pair_ids = pair_ids[:pair_len]
                    else:
                        if len(ids) > available_len:
                            ids = ids[:available_len]
                
                # Combine sequences
                if pair_ids is not None:
                    sequence = [bos] + ids + [eos, eos] + pair_ids + [eos]
                else:
                    sequence = [bos] + ids + [eos]
                    
                encoded_inputs = {
                    "input_ids": sequence,
                    "attention_mask": [1] * len(sequence)
                }
                
                # Padding
                if padding and max_length is not None and len(sequence) < max_length:
                    pad_id = self.pad_token_id if self.pad_token_id is not None else 1
                    sequence = sequence + [pad_id] * (max_length - len(sequence))
                    encoded_inputs["input_ids"] = sequence
                    encoded_inputs["attention_mask"] = [1] * len(encoded_inputs["input_ids"])
                    
                return BatchEncoding(encoded_inputs, tensor_type=return_tensors, prepend_batch_axis=prepend_batch_axis)

            PreTrainedTokenizerBase.prepare_for_model = prepare_for_model_patch
            logger.info("[patch] Fast Tokenizer prepare_for_model 패치 적용 완료 (백엔드)")
        except Exception as e:
            logger.warning("[patch] prepare_for_model 패치 적용 실패 (백엔드): " + str(e))

        from FlagEmbedding import FlagReranker
        path = settings.reranker_model_abs_path
        logger.info("[모델 로드] BGE-Reranker: " + path)
        _reranker = FlagReranker(path, use_fp16=settings.use_fp16)
    return _reranker