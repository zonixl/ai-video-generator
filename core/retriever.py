"""检索模块：封装多种检索策略。"""

import logging
import numpy as np

logger = logging.getLogger(__name__)


class Retriever:
    """检索器，支持 similarity 和 MMR 策略。"""

    def __init__(self, vector_store, embedder, strategy: str = "mmr",
                 top_k: int = 5, mmr_lambda: float = 0.6):
        self._vs = vector_store
        self._embedder = embedder
        self._strategy = strategy
        self._top_k = top_k
        self._mmr_lambda = mmr_lambda
        logger.info("Retriever initialized: strategy=%s top_k=%d mmr_lambda=%.2f",
                    strategy, top_k, mmr_lambda)

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
        """检索入口，根据策略路由。"""
        k = top_k or self._top_k
        logger.debug("Retriever.retrieve: query='%s' strategy=%s top_k=%d", query[:80], self._strategy, k)
        if self._strategy == "similarity":
            return self._similarity_search(query, k)
        elif self._strategy == "mmr":
            return self._mmr_search(query, k, self._mmr_lambda)
        else:
            raise ValueError(f"Unknown strategy: {self._strategy}")

    def _similarity_search(self, query: str, top_k: int) -> list[dict]:
        """纯相似度检索。"""
        return self._vs.search(query, top_k=top_k)

    def _mmr_search(self, query: str, top_k: int,
                    lambda_param: float = 0.6) -> list[dict]:
        """最大边际相关检索：兼顾相关性和多样性。"""
        # 先召回 2x 候选
        candidates = self._vs.search(query, top_k=top_k * 2)

        if len(candidates) <= top_k:
            logger.debug("MMR: only %d candidates, returning all", len(candidates))
            return candidates

        # 获取所有候选的向量
        candidate_texts = [d["text"] for d in candidates]
        candidate_vecs = np.array(self._embedder.embed(candidate_texts))
        query_vec = np.array(self._embedder.embed_query(query))

        selected = []
        remaining = list(range(len(candidates)))

        # 第一个选最相似的
        sim_to_query = np.dot(candidate_vecs, query_vec)
        first_idx = int(np.argmax(sim_to_query))
        selected.append(remaining.pop(first_idx))
        candidate_vecs = np.delete(candidate_vecs, first_idx, axis=0)

        while len(selected) < top_k and remaining:
            mmr_scores = []
            for i in range(len(candidate_vecs)):
                relevance = np.dot(candidate_vecs[i], query_vec)
                if selected:
                    sim_to_selected = max(
                        np.dot(candidate_vecs[i], np.array(self._embedder.embed_query(
                            candidates[s]["text"]
                        )))
                        for s in selected
                    )
                else:
                    sim_to_selected = 0
                mmr = lambda_param * relevance - (1 - lambda_param) * sim_to_selected
                mmr_scores.append(mmr)

            best_idx = int(np.argmax(mmr_scores))
            selected.append(remaining.pop(best_idx))
            candidate_vecs = np.delete(candidate_vecs, best_idx, axis=0)

        logger.debug("MMR: selected %d from %d candidates (lambda=%.2f)",
                     len(selected), len(candidates), lambda_param)
        return [candidates[i] for i in selected]
