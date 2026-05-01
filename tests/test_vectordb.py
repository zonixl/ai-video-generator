"""向量数据库模块测试。"""

import tempfile
import shutil
from pathlib import Path

import pytest


class FakeEmbedder:
    """简单的假 embedder，兼容 LangChain embeddings 接口。"""
    def embed_documents(self, texts):
        import random
        return [[random.random() for _ in range(128)] for _ in texts]

    def embed_query(self, text):
        import random
        return [random.random() for _ in range(128)]


def test_add_and_search():
    from core.vectordb import VectorStore

    tmpdir = tempfile.mkdtemp()
    try:
        embedder = FakeEmbedder()
        vs = VectorStore(tmpdir, "test_collection", embedder=embedder)

        ids = vs.add_texts(
            ["这是一段关于人工智能的文本", "这是关于烹饪的内容", "机器学习是AI的分支"],
            metadatas=[
                {"source": "test1.mp3"},
                {"source": "test2.mp3"},
                {"source": "test1.mp3"},
            ],
        )
        assert len(ids) == 3
        assert vs.count() == 3

        results = vs.search("人工智能", top_k=2)
        assert len(results) == 2
        assert "text" in results[0]
        assert "score" in results[0]
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_delete():
    from core.vectordb import VectorStore

    tmpdir = tempfile.mkdtemp()
    try:
        embedder = FakeEmbedder()
        vs = VectorStore(tmpdir, "test_delete", embedder=embedder)
        ids = vs.add_texts(["测试文本1", "测试文本2"],
                          metadatas=[{"idx": "1"}, {"idx": "2"}])
        assert vs.count() == 2

        vs.delete_by_ids([ids[0]])
        assert vs.count() == 1
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
