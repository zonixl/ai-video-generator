"""向量数据库模块：ChromaDB 封装。"""

import logging
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB 向量存储，本地持久化。"""

    def __init__(self, persist_dir: str | Path, collection_name: str,
                 embedder=None):
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        self._persist_dir = Path(persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._collection_name = collection_name
        self._embedder = embedder

        logger.debug("Connecting to ChromaDB: persist_dir=%s collection=%s",
                     self._persist_dir, collection_name)
        self._client = chromadb.PersistentClient(
            path=str(self._persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
        )
        logger.info("VectorStore ready: collection=%s count=%d", collection_name, self.count())

    def add_texts(self, texts: list[str], metadatas: list[dict] | None = None,
                  ids: list[str] | None = None) -> list[str]:
        """添加文本到向量库，自动生成 embedding。"""
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        if metadatas is None:
            metadatas = [{} for _ in texts]

        if self._embedder is None:
            raise RuntimeError("Embedder not set; must provide embedder for add_texts")

        logger.debug("Embedding %d texts for vector store...", len(texts))
        embeddings = self._embedder.embed(texts)
        logger.debug("Adding %d docs to collection...", len(texts))
        self._collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("Added %d documents to vectordb", len(ids))
        return ids

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """语义搜索，返回最相关文档。"""
        if self._embedder is None:
            raise RuntimeError("Embedder not set")

        logger.debug("Searching: query='%s' top_k=%d", query[:80], top_k)
        query_vector = self._embedder.embed_query(query)
        results = self._collection.query(
            query_embeddings=[query_vector],
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

    def delete_by_ids(self, ids: list[str]) -> int:
        """按 ID 删除文档。"""
        self._collection.delete(ids=ids)
        logger.info("Deleted %d documents", len(ids))
        return len(ids)

    def delete_by_file(self, source_file: str) -> int:
        """按来源文件删除所有关联文档。"""
        results = self._collection.get(where={"source": source_file})
        if results["ids"]:
            self._collection.delete(ids=results["ids"])
            logger.info("Deleted %d documents from source=%s", len(results["ids"]), source_file)
            return len(results["ids"])
        return 0

    def check_hash_exists(self, file_hash: str) -> bool:
        """检查指定 hash 的文件是否已入库。"""
        results = self._collection.get(where={"file_hash": file_hash}, limit=1)
        return bool(results["ids"])

    def delete_by_hash(self, file_hash: str) -> int:
        """按文件 hash 删除所有关联文档。"""
        results = self._collection.get(where={"file_hash": file_hash})
        if results["ids"]:
            self._collection.delete(ids=results["ids"])
            logger.info("Deleted %d documents from hash=%s", len(results["ids"]), file_hash)
            return len(results["ids"])
        return 0

    def count(self) -> int:
        return self._collection.count()

    def get_all(self) -> dict:
        return self._collection.get()
