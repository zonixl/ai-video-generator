"""摄入管道集成测试（需要真实模型，默认跳过）。"""

import pytest


@pytest.mark.skip(reason="需要真实STT/Embedding模型，仅手动执行")
def test_ingest_pipeline():
    from config import Settings
    from core.stt import SpeechToText
    from core.embedder import Embedder
    from core.vectordb import VectorStore
    from pipeline.ingest import IngestPipeline

    cfg = Settings()
    stt = SpeechToText(cfg.stt_model_size, cfg.stt_device, cfg.stt_compute_type)
    embedder = Embedder(cfg.embedding_model_name, cfg.embedding_device)
    vs = VectorStore(cfg.vectordb_persist_dir, cfg.vectordb_collection_name, embedder)

    pipeline = IngestPipeline(stt, embedder, vs, cfg)
    result = pipeline.run("test.mp3")

    assert result["chunks"] > 0
    assert len(result["ids"]) > 0
    assert result["total_chars"] > 0
