"""语音识别模块：faster_whisper 封装。"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SpeechToText:
    """封装 faster_whisper，提供 transcribe 接口。"""

    def __init__(self, model_size: str = "medium", device: str = "cuda",
                 compute_type: str = "float16", language: str | None = None):
        from faster_whisper import WhisperModel
        device, compute_type = self._resolve_runtime(device, compute_type)
        logger.info("Loading STT model: size=%s device=%s compute=%s", model_size, device, compute_type)
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self._language = language
        logger.debug("STT model loaded successfully")

    @staticmethod
    def _resolve_runtime(device: str, compute_type: str) -> tuple[str, str]:
        if device != "cuda":
            return device, compute_type

        try:
            import ctranslate2
            cuda_count = ctranslate2.get_cuda_device_count()
        except Exception as exc:
            logger.warning("Could not check CTranslate2 CUDA availability: %s", exc)
            cuda_count = 0

        if cuda_count > 0:
            return device, compute_type

        fallback_compute = "int8" if compute_type == "float16" else compute_type
        logger.warning(
            "CUDA not available for faster-whisper, falling back to CPU (compute_type=%s)",
            fallback_compute,
        )
        return "cpu", fallback_compute

    def transcribe(self, audio_path: str | Path) -> list[dict]:
        """转写音频，返回带时间戳的 segment 列表。"""
        logger.info("Transcribing: %s", Path(audio_path).name)
        segments, info = self._model.transcribe(
            str(audio_path),
            language=self._language,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        logger.debug("Detected language: %s (p=%.2f)", info.language, info.language_probability)

        results = []
        for seg in segments:
            results.append({
                "text": seg.text.strip(),
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "confidence": round(seg.avg_logprob, 4) if seg.avg_logprob else 0.0,
            })
        logger.info("Transcription done: %d segments, %d chars", len(results), sum(len(r["text"]) for r in results))
        return results
