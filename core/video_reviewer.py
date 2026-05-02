"""已生成视频的多模态视觉审查。"""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from core import prompts
from core.vision_provider import VisionProvider
from utils.file_utils import write_json
from utils.media_utils import safe_stem

logger = logging.getLogger(__name__)


@dataclass
class VideoReviewResult:
    video_path: str
    review_path: str
    frames_dir: str
    duration: float
    frame_paths: list[str]


class FFmpegFrameExtractor:
    """使用 ffprobe/ffmpeg 从视频中抽取审查关键帧。"""

    def __init__(self, max_width: int = 768):
        self._max_width = max(256, int(max_width))

    def probe_duration(self, video_path: str | Path) -> float:
        ffprobe = shutil.which("ffprobe") or shutil.which("ffprobe.exe") or "ffprobe"
        command = [
            ffprobe,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]
        result = subprocess.run(
            command,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {result.stderr}")
        return float((result.stdout or "0").strip() or 0)

    def extract_frames(self, video_path: str | Path, output_dir: str | Path, frame_count: int) -> tuple[float, list[Path]]:
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        duration = self.probe_duration(video_path)
        frames: list[Path] = []
        for index, seconds in enumerate(sample_times(duration, frame_count), start=1):
            output = output_dir / f"frame_{index:02d}_{seconds:.1f}s.jpg"
            self._extract_one(video_path, output, seconds)
            frames.append(output)
        return duration, frames

    def _extract_one(self, video_path: Path, output_path: Path, seconds: float) -> None:
        ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe") or "ffmpeg"
        command = [
            ffmpeg,
            "-y",
            "-ss", f"{seconds:.3f}",
            "-i", str(video_path),
            "-frames:v", "1",
            "-vf", f"scale={self._max_width}:-2",
            "-q:v", "2",
            str(output_path),
        ]
        result = subprocess.run(
            command,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg frame extract failed: {result.stderr}")


class VideoReviewer:
    """审查任意已生成 MP4，不依赖 Remotion DSL。"""

    def __init__(
        self,
        *,
        vision_provider: VisionProvider,
        output_dir: str | Path,
        extractor: FFmpegFrameExtractor | None = None,
        max_frame_width: int = 768,
    ):
        self._vision_provider = vision_provider
        self._output_dir = Path(output_dir)
        self._extractor = extractor or FFmpegFrameExtractor(max_width=max_frame_width)

    def review(
        self,
        video_path: str | Path,
        *,
        job_id: str | None = None,
        frame_count: int = 7,
        prompt: str | None = None,
    ) -> VideoReviewResult:
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(video_path)

        job_id = job_id or safe_stem(video_path.stem, fallback="video_review", limit=80)
        review_dir = self._output_dir / job_id
        frames_dir = review_dir / "frames"
        review_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Video review start: video=%s frames=%d output=%s", video_path, frame_count, review_dir)
        duration, frame_paths = self._extractor.extract_frames(video_path, frames_dir, frame_count)
        final_prompt = prompt or prompts.REVIEW_VIDEO_FRAMES.format(
            video_name=video_path.name,
            duration=f"{duration:.1f}",
            frame_count=len(frame_paths),
        )
        review_text = self._vision_provider.review(final_prompt, frame_paths)

        review_path = review_dir / "review.md"
        review_path.write_text(review_text, encoding="utf-8")
        metadata = {
            "video_path": str(video_path),
            "duration": duration,
            "frame_paths": [str(path) for path in frame_paths],
            "review_path": str(review_path),
        }
        write_json(review_dir / "review_meta.json", metadata)
        logger.info("Video review done: %s", review_path)
        return VideoReviewResult(
            video_path=str(video_path),
            review_path=str(review_path),
            frames_dir=str(frames_dir),
            duration=duration,
            frame_paths=[str(path) for path in frame_paths],
        )


def sample_times(duration: float, frame_count: int) -> list[float]:
    """返回覆盖首尾和中段的抽帧时间点。"""
    duration = max(0.0, float(duration))
    frame_count = max(1, int(frame_count))
    if duration <= 0:
        return [0.0]
    if frame_count == 1:
        return [min(duration - 0.1, duration * 0.5)]

    start_ratio = 0.08
    end_ratio = 0.92
    ratios = [
        start_ratio + (end_ratio - start_ratio) * index / (frame_count - 1)
        for index in range(frame_count)
    ]
    max_time = max(duration - 0.1, 0.0)
    times: list[float] = []
    for ratio in ratios:
        seconds = max(0.0, min(max_time, duration * ratio))
        if all(abs(seconds - item) > 0.25 for item in times):
            times.append(seconds)
    return times or [0.0]
