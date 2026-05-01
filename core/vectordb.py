"""向量数据库模块：LangChain Chroma 封装。"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB 向量存储，委托给 langchain_chroma.Chroma。"""

    def __init__(self, persist_dir: str | Path, collection_name: str,
                 embedder=None):
        import chromadb
        from langchain_chroma import Chroma

        self._persist_dir = Path(persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._collection_name = collection_name

        self._client = chromadb.PersistentClient(path=str(self._persist_dir))

        # 接受多种 embedder 形式：Embedder 包装类、原始 embeddings 实例、或有 embed_query 的对象
        if embedder is not None and hasattr(embedder, '_embeddings'):
            embedding_function = embedder._embeddings
        else:
            embedding_function = embedder

        self._store = Chroma(
            client=self._client,
            collection_name=collection_name,
            embedding_function=embedding_function,
        )
        logger.info("VectorStore ready: collection=%s count=%d", collection_name, self.count())

    # ---- 写入 ----
    def add_texts(self, texts: list[str], metadatas: list[dict] | None = None,
                  ids: list[str] | None = None) -> list[str]:
        """添加文本到向量库，embedding 由 Chroma 内部自动生成。"""
        logger.debug("Adding %d docs via Chroma.add_texts ...", len(texts))
        result = self._store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        logger.info("Added %d documents to vectordb", len(result))
        return result

    # ---- 查询 ----
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """语义搜索，返回最相关文档（带距离分数和 ID）。"""
        logger.debug("Searching: query='%s' top_k=%d", query[:80], top_k)
        query_embedding = self._store._embedding_function.embed_query(query)
        results = self._store._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        docs = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                docs.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": round(results["distances"][0][i], 4) if results["distances"] else 0,
                })
        logger.debug("Search returned %d results", len(docs))
        return docs

    # ---- 删除 ----
    def delete_by_ids(self, ids: list[str]) -> int:
        self._store.delete(ids=ids)
        logger.info("Deleted %d documents", len(ids))
        return len(ids)

    def delete_by_file(self, source_file: str) -> int:
        results = self._store._collection.get(where={"source": source_file})
        if results["ids"]:
            self._store.delete(ids=results["ids"])
            logger.info("Deleted %d documents from source=%s", len(results["ids"]), source_file)
            return len(results["ids"])
        return 0

    def delete_by_hash(self, file_hash: str) -> int:
        results = self._store._collection.get(where={"file_hash": file_hash})
        if results["ids"]:
            self._store.delete(ids=results["ids"])
            logger.info("Deleted %d documents from hash=%s", len(results["ids"]), file_hash)
            return len(results["ids"])
        return 0

    def check_hash_exists(self, file_hash: str) -> bool:
        results = self._store._collection.get(where={"file_hash": file_hash}, limit=1)
        return bool(results["ids"])

    # ---- 统计 ----
    def count(self) -> int:
        return self._store._collection.count()

    def get_all(self) -> dict:
        return self._store._collection.get()
