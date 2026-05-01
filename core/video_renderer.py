"""图片动画和最终视频合成。"""

from __future__ import annotations

import logging
from pathlib import Path
import textwrap
import time

from core.schema import AudioAsset, ClipAsset, ImageAsset, Scene, VideoPlan
from utils.media_utils import scene_filename

logger = logging.getLogger(__name__)


def _import_moviepy():
    """兼容 moviepy 1.x 和 2.x 的导入方式。"""
    try:
        from moviepy import AudioFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips
    except ImportError:
        from moviepy.editor import AudioFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips
    return AudioFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips


class VideoRenderer:
    """把图片、字幕和音频合成为竖屏视频。"""

    def render_scene(
        self,
        scene: Scene,
        image: ImageAsset,
        output_dir: str | Path,
        *,
        width: int,
        height: int,
        fps: int,
    ) -> ClipAsset:
        """把单张分镜图片渲染为短视频片段。"""
        start = time.perf_counter()
        AudioFileClip, CompositeVideoClip, ImageClip, _ = _import_moviepy()
        del AudioFileClip

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / scene_filename(scene.index, ".mp4")
        logger.info(
            "VideoRenderer.render_scene start: scene=%03d image=%s output=%s size=%dx%d fps=%d duration=%.1fs",
            scene.index, image.path, output_path, width, height, fps, scene.duration,
        )

        base_clip = ImageClip(str(image.path))
        base_clip = self._with_duration(base_clip, scene.duration)
        base_clip = self._fit_and_animate(base_clip, image.path, scene, width, height)

        subtitle_path = output_dir / scene_filename(scene.index, "_subtitle.png")
        self._create_subtitle_overlay(scene.subtitle, subtitle_path, width, height)
        subtitle_clip = ImageClip(str(subtitle_path))
        subtitle_clip = self._with_duration(subtitle_clip, scene.duration)
        subtitle_clip = self._with_position(subtitle_clip, (0, 0))

        clip = CompositeVideoClip([base_clip, subtitle_clip], size=(width, height))
        clip = self._with_duration(clip, scene.duration)
        clip = self._with_fps(clip, fps)
        clip.write_videofile(
            str(output_path),
            fps=fps,
            codec="libx264",
            audio=False,
            ffmpeg_params=["-pix_fmt", "yuv420p"],
            logger="bar",
        )
        self._close_clips(clip, base_clip, subtitle_clip)
        logger.info(
            "VideoRenderer.render_scene done: scene=%03d output=%s elapsed=%.1fs",
            scene.index, output_path, time.perf_counter() - start,
        )
        return ClipAsset(scene_index=scene.index, path=str(output_path), duration=scene.duration)

    def compose(
        self,
        plan: VideoPlan,
        clips: list[ClipAsset],
        output_path: str | Path,
        *,
        audio: AudioAsset | None = None,
    ) -> str:
        """拼接片段并挂载可选音频。"""
        start = time.perf_counter()
        AudioFileClip, _, _, concatenate_videoclips = _import_moviepy()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(
            "VideoRenderer.compose start: clips=%d audio=%s output=%s fps=%d duration=%.1fs",
            len(clips), bool(audio), output_path, plan.fps, plan.total_duration,
        )

        video_clips = []
        for index, clip in enumerate(clips, start=1):
            logger.info("      loading clip [%d/%d]: %s", index, len(clips), clip.path)
            video_clips.append(self._with_fps(self._load_video_clip(clip.path), plan.fps))
        final_clip = concatenate_videoclips(video_clips, method="compose")
        audio_clip = None
        if audio:
            logger.info("      attaching audio: %s", audio.path)
            audio_clip = AudioFileClip(audio.path)
            final_clip = self._with_audio(final_clip, audio_clip)

        final_clip.write_videofile(
            str(output_path),
            fps=plan.fps,
            codec="libx264",
            audio_codec="aac" if audio else None,
            ffmpeg_params=["-pix_fmt", "yuv420p"],
            logger="bar",
        )
        self._close_clips(final_clip, audio_clip, *video_clips)
        logger.info("VideoRenderer.compose done: output=%s elapsed=%.1fs", output_path, time.perf_counter() - start)
        return str(output_path)

    def _load_video_clip(self, path: str):
        try:
            from moviepy import VideoFileClip
        except ImportError:
            from moviepy.editor import VideoFileClip
        return VideoFileClip(str(path))

    def _fit_and_animate(self, clip, image_path: str, scene: Scene, width: int, height: int):
        from PIL import Image

        with Image.open(image_path) as image:
            image_width, image_height = image.size
        cover_scale = max(width / image_width, height / image_height)

        def scale_at(t: float) -> float:
            progress = min(max(t / max(scene.duration, 0.1), 0.0), 1.0)
            if scene.animation == "zoom_out":
                return cover_scale * (1.08 - 0.08 * progress)
            if scene.animation in {"zoom_in", "fade"}:
                return cover_scale * (1.0 + 0.08 * progress)
            return cover_scale * 1.06

        def position_at(t: float):
            progress = min(max(t / max(scene.duration, 0.1), 0.0), 1.0)
            scale = scale_at(t)
            scaled_width = image_width * scale
            scaled_height = image_height * scale
            x = (width - scaled_width) / 2
            y = (height - scaled_height) / 2
            if scene.animation == "pan_left":
                x += 40 * (1 - 2 * progress)
            elif scene.animation == "pan_right":
                x += 40 * (2 * progress - 1)
            return x, y

        try:
            clip = self._resize(clip, scale_at)
            clip = self._with_position(clip, position_at)
        except Exception:
            logger.debug("Dynamic animation failed; falling back to static cover fit", exc_info=True)
            clip = self._resize(clip, cover_scale)
            clip = self._with_position(clip, ("center", "center"))
        return clip

    def _create_subtitle_overlay(self, text: str, output_path: Path, width: int, height: int) -> None:
        from PIL import Image, ImageDraw, ImageFont

        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        font = self._font(ImageFont, 48)
        lines = textwrap.wrap(text.strip(), width=18, break_long_words=True)[:3]
        box_margin = int(width * 0.08)
        box_height = 78 * max(1, len(lines)) + 42
        box_top = int(height * 0.78)
        draw.rounded_rectangle(
            (box_margin, box_top, width - box_margin, box_top + box_height),
            radius=28,
            fill=(0, 0, 0, 150),
        )
        y = box_top + 24
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = (width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            y += 76
        image.save(output_path)

    def _font(self, image_font, size: int):
        candidates = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]
        for path in candidates:
            if Path(path).exists():
                return image_font.truetype(path, size=size)
        return image_font.load_default()

    def _with_duration(self, clip, duration: float):
        if hasattr(clip, "with_duration"):
            return clip.with_duration(duration)
        return clip.set_duration(duration)

    def _with_fps(self, clip, fps: int):
        if hasattr(clip, "with_fps"):
            return clip.with_fps(fps)
        return clip.set_fps(fps)

    def _with_position(self, clip, position):
        if hasattr(clip, "with_position"):
            return clip.with_position(position)
        return clip.set_position(position)

    def _with_audio(self, clip, audio_clip):
        if hasattr(clip, "with_audio"):
            return clip.with_audio(audio_clip)
        return clip.set_audio(audio_clip)

    def _resize(self, clip, value):
        if hasattr(clip, "resized"):
            return clip.resized(value)
        return clip.resize(value)

    def _close_clips(self, *clips) -> None:
        for clip in clips:
            if clip is not None and hasattr(clip, "close"):
                clip.close()

