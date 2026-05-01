"""Embedding模型封装：sentence-transformers / BGE。"""

import logging
import torch

logger = logging.getLogger(__name__)


class Embedder:
    """本地 Embedding 模型，基于 sentence-transformers。"""

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5", device: str = "cuda",
                 normalize: bool = True):
        from sentence_transformers import SentenceTransformer
        device = self._resolve_device(device)
        logger.info("Loading embedding model: %s (device=%s)", model_name, device)
        self._model = SentenceTransformer(model_name, device=device)
        self._normalize = normalize
        self._model_name = model_name
        logger.info("Embedding model loaded: dim=%d", self.dimension)

    @staticmethod
    def _resolve_device(device: str) -> str:
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA not available for PyTorch, falling back to CPU")
            return "cpu"
        return device

    def embed(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """批量向量化。"""
        if isinstance(texts, str):
            texts = [texts]
        logger.debug("Embedding %d texts (batch_size=%d)", len(texts), batch_size)
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=self._normalize,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        """单条查询向量化。"""
        return self.embed([text])[0]

    @property
    def dimension(self) -> int:
        return self._model.get_embedding_dimension()
