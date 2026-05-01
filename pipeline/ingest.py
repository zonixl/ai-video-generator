"""摄入管道：音频 → 语音识别 → LLM重构 → 文本分段 → Embedding → 向量库。"""

import logging
import time
from pathlib import Path

from core import prompts
from utils.audio_utils import split_by_silence
from utils.text_utils import clean_text, chunk_by_paragraphs
from utils.file_utils import save_transcript, write_text, file_hash

logger = logging.getLogger(__name__)


class IngestPipeline:
    """编排音频摄入全流程。"""

    def __init__(self, stt, embedder, vector_store, model_manager, config):
        self._stt = stt
        self._embedder = embedder
        self._vs = vector_store
        self._mgr = model_manager
        self._cfg = config

    def run(self, audio_path: str, force: bool = False) -> dict:
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        logger.info("=" * 50)
        logger.info("IngestPipeline START: %s", audio_path.name)

        fhash = file_hash(audio_path)
        logger.debug("File hash: %s", fhash)

        # ---- 去重检查 ----
        if self._vs.check_hash_exists(fhash):
            if not force:
                logger.warning("Duplicate detected! hash=%s already in vectordb. Use --force to re-ingest.", fhash)
                return {"chunks": 0, "ids": [], "skipped": True, "hash": fhash,
                        "raw_chars": 0, "restructured_chars": 0,
                        "raw_transcript_path": "", "restructured_path": ""}
            logger.info("Force re-ingest: removing old entries for hash=%s", fhash)
            self._vs.delete_by_hash(fhash)

        # ---- Step 1: 音频分片 ----
        t0 = time.time()
        logger.info("[1/5] Audio splitting: %s", audio_path.name)
        chunks = split_by_silence(
            audio_path,
            silence_threshold=self._cfg.audio_silence_threshold,
            min_silence_duration=self._cfg.audio_min_silence_duration,
        )
        logger.info("      -> %d chunks (%.1fs)", len(chunks), time.time() - t0)

        # ---- Step 2: 语音识别 ----
        t0 = time.time()
        logger.info("[2/5] Speech-to-text ...")
        all_segments = []
        for i, chunk_path in enumerate(chunks):
            segments = self._stt.transcribe(chunk_path)
            all_segments.extend(segments)
            logger.debug("      chunk %d/%d: %d segments, %d chars",
                        i + 1, len(chunks), len(segments),
                        sum(len(s["text"]) for s in segments))

        raw_text = "\n".join(s["text"] for s in all_segments if s["text"])
        raw_text = clean_text(raw_text)

        # 保存原始转写
        raw_transcript_path = save_transcript(
            raw_text, audio_path, self._cfg.output_transcripts_dir
        )
        logger.info("      -> raw transcript saved: %s", raw_transcript_path.name)
        logger.info("      -> raw: %d chars, %d segments (%.1fs)",
                    len(raw_text), len(all_segments), time.time() - t0)

        # ---- Step 3: LLM 分析重构 ----
        t0 = time.time()
        logger.info("[3/5] LLM restructuring (model=summarizer) ...")
        restructured_text = self._restructure(raw_text)
        logger.info("      -> restructured: %d chars (%.1fs)",
                    len(restructured_text), time.time() - t0)
        logger.debug("Restructured preview: %s...", restructured_text[:200])

        # 保存重构版本
        restructured_path = raw_transcript_path.parent / raw_transcript_path.name.replace(".txt", "_restructured.md")
        write_text(restructured_path, restructured_text)
        logger.info("      -> restructured saved: %s", restructured_path.name)

        # ---- Step 4: 文本分chunk ----
        t0 = time.time()
        logger.info("[4/5] Text chunking (size=%d, overlap=%d) ...",
                    self._cfg.text_chunk_size, self._cfg.text_chunk_overlap)
        text_chunks = chunk_by_paragraphs(
            restructured_text,
            chunk_size=self._cfg.text_chunk_size,
            overlap=self._cfg.text_chunk_overlap,
        )
        logger.info("      -> %d chunks (%.1fs)", len(text_chunks), time.time() - t0)

        # ---- Step 5: Embedding + 入库 ----
        t0 = time.time()
        logger.info("[5/5] Embedding + storing to vectordb ...")
        metadatas = []
        for i, chunk in enumerate(text_chunks):
            metadatas.append({
                "source": str(audio_path.resolve()),
                "source_name": audio_path.name,
                "chunk_index": i,
                "total_chunks": len(text_chunks),
                "file_hash": fhash,
                "restructured": True,
                "raw_chars": len(raw_text),
                "restructured_chars": len(restructured_text),
            })

        ids = self._vs.add_texts(text_chunks, metadatas)
        logger.info("      -> stored: %d documents (%.1fs)", len(ids), time.time() - t0)

        logger.info("IngestPipeline DONE: chunks=%d raw_chars=%d restructured_chars=%d",
                    len(text_chunks), len(raw_text), len(restructured_text))
        return {
            "chunks": len(text_chunks),
            "ids": ids,
            "raw_transcript_path": str(raw_transcript_path),
            "restructured_path": str(restructured_path),
            "segment_count": len(all_segments),
            "raw_chars": len(raw_text),
            "restructured_chars": len(restructured_text),
        }

    def _restructure(self, raw_text: str) -> str:
        """调用 LLM 修正识别错误 + 结构化重组。"""
        if len(raw_text) < 100:
            logger.info("Text too short (<100 chars), skipping restructure")
            return raw_text

        user_prompt = prompts.RESTRUCTURE_TRANSCRIPT.format(transcript=raw_text)

        try:
            result = self._mgr.generate(
                "summarizer",
                user_prompt,
                system_prompt=prompts.SYSTEM_RESTRUCTURE,
            )
            return result.strip() or raw_text
        except Exception as e:
            logger.warning("LLM restructure failed: %s, keeping raw text", e)
            return raw_text
