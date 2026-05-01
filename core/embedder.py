"""Embedding模型封装：委托给 LangChain 的 HuggingFaceEmbeddings。"""

import logging
import torch

logger = logging.getLogger(__name__)


class Embedder:
    """本地 Embedding 模型，基于 langchain_community HuggingFaceEmbeddings。"""

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5", device: str = "cuda",
                 normalize: bool = True):
        from langchain_huggingface.embeddings import HuggingFaceEmbeddings

        device = self._resolve_device(device)
        logger.info("Loading embedding model: %s (device=%s)", model_name, device)
        self._embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": normalize},
        )
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
        return self._embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        """单条查询向量化。"""
        return self._embeddings.embed_query(text)

    @property
    def dimension(self) -> int:
        return self._embeddings._client.get_embedding_dimension()
