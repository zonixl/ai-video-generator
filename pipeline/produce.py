"""多媒体生产管道：文案 → 分镜 → 图片 → 动画 → 视频。"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from core.image_provider import ImageProvider, PlaceholderImageProvider
from core.scene_splitter import RuleBasedSceneSplitter
from core.schema import AudioAsset, ClipAsset, ImageAsset, ProduceResult, VideoPlan, to_dict
from core.tts import EdgeTTSProvider, TTSProvider
from core.video_renderer import VideoRenderer
from utils.file_utils import read_text, write_json
from utils.media_utils import make_job_id, scene_filename
from utils.subtitle_utils import write_srt

logger = logging.getLogger(__name__)


class ProducePipeline:
    """编排低成本文案到视频生产流程。"""

    def __init__(
        self,
        config,
        *,
        splitter: RuleBasedSceneSplitter | None = None,
        image_provider: ImageProvider | None = None,
        tts_provider: TTSProvider | None = None,
        renderer: VideoRenderer | None = None,
    ):
        self._cfg = config
        self._splitter = splitter or RuleBasedSceneSplitter(
            min_scene_duration=getattr(config, "video_min_scene_duration", 5.0),
            max_scene_duration=getattr(config, "video_max_scene_duration", 8.0),
            chars_per_second=getattr(config, "video_chars_per_second", 4.5),
        )
        self._image_provider = image_provider or PlaceholderImageProvider()
        self._tts_provider = tts_provider or EdgeTTSProvider()
        self._renderer = renderer or VideoRenderer()

    def run(
        self,
        script_path: str,
        *,
        output_path: str | None = None,
        title: str | None = None,
        style: str = "clean",
        width: int | None = None,
        height: int | None = None,
        fps: int | None = None,
        use_tts: bool = False,
        reuse_assets: bool = False,
    ) -> ProduceResult:
        """从文案文件生成视频。"""
        total_start = time.perf_counter()
        script = read_text(script_path)
        width = width or self._cfg.video_width
        height = height or self._cfg.video_height
        fps = fps or self._cfg.video_fps
        job_id = make_job_id("video")
        logger.info("=" * 50)
        logger.info(
            "ProducePipeline START: script=%s job_id=%s size=%dx%d fps=%d tts=%s reuse_assets=%s",
            script_path, job_id, width, height, fps, use_tts, reuse_assets,
        )

        step_start = time.perf_counter()
        logger.info("[1/7] Splitting script into scenes ...")
        plan = self._splitter.split(script, title=title, style=style, width=width, height=height, fps=fps)
        logger.info(
            "      -> %d scenes, estimated %.1fs (%.1fs)",
            len(plan.scenes), plan.total_duration, time.perf_counter() - step_start,
        )
        for scene in plan.scenes:
            logger.info(
                "      scene %03d: %.1fs animation=%s subtitle=%s",
                scene.index, scene.duration, scene.animation, self._preview(scene.subtitle),
            )

        logger.info("[2/7] %s", "Generating TTS audio ..." if use_tts else "Skipping TTS audio (--no-tts)")
        audio_asset = self._synthesize_audio(plan, job_id) if use_tts else None
        if audio_asset and audio_asset.duration > 0 and plan.total_duration > 0:
            before_duration = plan.total_duration
            self._scale_scene_durations(plan, audio_asset.duration)
            logger.info(
                "      -> scaled scene durations: %.1fs -> %.1fs",
                before_duration, plan.total_duration,
            )

        step_start = time.perf_counter()
        logger.info("[3/7] Saving video plan JSON ...")
        plan_path = self._cfg.output_plans_dir / f"{job_id}.json"
        write_json(plan_path, to_dict(plan))
        logger.info("      -> %s (%.1fs)", plan_path, time.perf_counter() - step_start)

        logger.info("[4/7] Generating images ...")
        image_assets = self._generate_images(plan, job_id, reuse_assets=reuse_assets)
        logger.info("[5/7] Rendering animated scene clips ...")
        clip_assets = self._render_clips(plan, image_assets, job_id, reuse_assets=reuse_assets)

        step_start = time.perf_counter()
        logger.info("[6/7] Writing subtitles ...")
        subtitle_path = self._cfg.output_subtitles_dir / f"{job_id}.srt"
        write_srt(plan, subtitle_path, max_chars=self._cfg.video_subtitle_max_chars)
        logger.info("      -> %s (%.1fs)", subtitle_path, time.perf_counter() - step_start)

        step_start = time.perf_counter()
        logger.info("[7/7] Composing final video ...")
        final_path = Path(output_path) if output_path else self._cfg.output_videos_dir / f"{job_id}.mp4"
        video_path = self._renderer.compose(plan, clip_assets, final_path, audio=audio_asset)
        logger.info("      -> %s (%.1fs)", video_path, time.perf_counter() - step_start)
        logger.info(
            "ProducePipeline DONE: video=%s scenes=%d duration=%.1fs elapsed=%.1fs",
            video_path, len(plan.scenes), plan.total_duration, time.perf_counter() - total_start,
        )

        return ProduceResult(
            job_id=job_id,
            video_path=video_path,
            plan_path=str(plan_path),
            subtitle_path=str(subtitle_path),
            image_paths=[asset.path for asset in image_assets],
            clip_paths=[asset.path for asset in clip_assets],
            audio_path=audio_asset.path if audio_asset else None,
        )

    def _synthesize_audio(self, plan: VideoPlan, job_id: str) -> AudioAsset:
        text = "\n".join(scene.narration for scene in plan.scenes)
        audio_path = self._cfg.output_audio_dir / f"{job_id}.mp3"
        start = time.perf_counter()
        logger.info(
            "      TTS input: chars=%d voice=%s rate=%.2f output=%s",
            len(text), self._cfg.tts_voice, self._cfg.tts_speed, audio_path,
        )
        asset = self._tts_provider.synthesize(
            text,
            audio_path,
            voice=self._cfg.tts_voice,
            rate=self._cfg.tts_speed,
        )
        logger.info("      -> audio %.1fs saved: %s (%.1fs)", asset.duration, asset.path, time.perf_counter() - start)
        return asset

    def _generate_images(self, plan: VideoPlan, job_id: str, *, reuse_assets: bool) -> list[ImageAsset]:
        image_dir = self._cfg.output_images_dir / job_id
        assets = []
        start = time.perf_counter()
        for position, scene in enumerate(plan.scenes, start=1):
            image_path = image_dir / scene_filename(scene.index, ".png")
            if reuse_assets and image_path.exists():
                logger.info("      [%d/%d] reuse image: %s", position, len(plan.scenes), image_path)
                assets.append(ImageAsset(scene.index, str(image_path), prompt=scene.image_prompt))
                continue
            scene_start = time.perf_counter()
            logger.info(
                "      [%d/%d] generating image for scene %03d: %s",
                position, len(plan.scenes), scene.index, self._preview(scene.image_prompt),
            )
            assets.append(
                self._image_provider.generate(scene, image_dir, width=plan.width, height=plan.height)
            )
            logger.info("            -> %s (%.1fs)", assets[-1].path, time.perf_counter() - scene_start)
        logger.info("      -> generated/reused %d images (%.1fs)", len(assets), time.perf_counter() - start)
        return assets

    def _render_clips(
        self,
        plan: VideoPlan,
        image_assets: list[ImageAsset],
        job_id: str,
        *,
        reuse_assets: bool,
    ) -> list[ClipAsset]:
        clip_dir = self._cfg.output_clips_dir / job_id
        assets = []
        images_by_scene = {asset.scene_index: asset for asset in image_assets}
        start = time.perf_counter()
        for position, scene in enumerate(plan.scenes, start=1):
            clip_path = clip_dir / scene_filename(scene.index, ".mp4")
            if reuse_assets and clip_path.exists():
                logger.info("      [%d/%d] reuse clip: %s", position, len(plan.scenes), clip_path)
                assets.append(ClipAsset(scene.index, str(clip_path), scene.duration))
                continue
            scene_start = time.perf_counter()
            logger.info(
                "      [%d/%d] rendering scene %03d: duration=%.1fs animation=%s",
                position, len(plan.scenes), scene.index, scene.duration, scene.animation,
            )
            assets.append(
                self._renderer.render_scene(
                    scene,
                    images_by_scene[scene.index],
                    clip_dir,
                    width=plan.width,
                    height=plan.height,
                    fps=plan.fps,
                )
            )
            logger.info("            -> %s (%.1fs)", assets[-1].path, time.perf_counter() - scene_start)
        logger.info("      -> rendered/reused %d clips (%.1fs)", len(assets), time.perf_counter() - start)
        return assets

    def _scale_scene_durations(self, plan: VideoPlan, target_duration: float) -> None:
        factor = target_duration / plan.total_duration
        for scene in plan.scenes:
            scene.duration = round(max(1.0, scene.duration * factor), 2)

    def _preview(self, text: str, limit: int = 48) -> str:
        text = " ".join(text.split())
        return text if len(text) <= limit else f"{text[:limit]}..."
