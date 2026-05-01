"""检索模块：委托给 LangChain Chroma 内置的 similarity / MMR 检索。"""

import logging

logger = logging.getLogger(__name__)


class Retriever:
    """检索器，支持 similarity 和 MMR 策略，使用 Chroma 内置实现。"""

    def __init__(self, vector_store, embedder=None, strategy: str = "mmr",
                 top_k: int = 5, mmr_lambda: float = 0.6):
        self._vs = vector_store
        self._strategy = strategy
        self._top_k = top_k
        self._mmr_lambda = mmr_lambda
        logger.info("Retriever initialized: strategy=%s top_k=%d mmr_lambda=%.2f",
                    strategy, top_k, mmr_lambda)

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
        """检索入口，根据策略路由。"""
        k = top_k or self._top_k
        logger.debug("Retriever.retrieve: query='%s' strategy=%s top_k=%d",
                     query[:80], self._strategy, k)

        if self._strategy == "similarity":
            return self._vs.search(query, top_k=k)
        elif self._strategy == "mmr":
            docs = self._vs._store.max_marginal_relevance_search(
                query, k=k, fetch_k=k * 2, lambda_mult=self._mmr_lambda
            )
            results = []
            for doc in docs:
                results.append({
                    "id": doc.metadata.get("id", ""),
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": 0.0,  # MMR 不返回分数
                })
            logger.debug("MMR: selected %d docs (lambda=%.2f)", len(results), self._mmr_lambda)
            return results
        else:
            raise ValueError(f"Unknown strategy: {self._strategy}")
