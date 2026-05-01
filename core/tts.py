"""TTS Provider。"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
import logging
from pathlib import Path

from core.schema import AudioAsset

logger = logging.getLogger(__name__)


class TTSProvider(ABC):
    """配音生成抽象接口。"""

    @abstractmethod
    def synthesize(self, text: str, output_path: str | Path, *, voice: str, rate: float = 1.0) -> AudioAsset:
        ...


class EdgeTTSProvider(TTSProvider):
    """基于 edge-tts 的低成本配音实现。"""

    provider_name = "edge-tts"

    def synthesize(self, text: str, output_path: str | Path, *, voice: str, rate: float = 1.0) -> AudioAsset:
        try:
            import edge_tts
        except ImportError as exc:
            raise RuntimeError("EdgeTTSProvider 需要安装 edge-tts") from exc

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rate_percent = int((rate - 1.0) * 100)
        rate_text = f"{rate_percent:+d}%"
        logger.info(
            "EdgeTTS start: chars=%d voice=%s rate=%s output=%s",
            len(text), voice, rate_text, output_path,
        )

        async def _run() -> None:
            communicate = edge_tts.Communicate(text, voice=voice, rate=rate_text)
            await communicate.save(str(output_path))

        asyncio.run(_run())
        duration = _audio_duration(output_path)
        logger.info("EdgeTTS done: duration=%.1fs output=%s", duration, output_path)
        return AudioAsset(
            path=str(output_path),
            duration=duration,
            provider=self.provider_name,
            voice=voice,
        )


def _audio_duration(path: str | Path) -> float:
    try:
        from moviepy import AudioFileClip
    except ImportError:
        try:
            from moviepy.editor import AudioFileClip
        except ImportError:
            return 0.0

    clip = AudioFileClip(str(path))
    try:
        return float(clip.duration or 0.0)
    finally:
        clip.close()

