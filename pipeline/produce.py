"""多媒体生产管道：文案 → 分镜 → 图片 → 动画 → 视频。"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from core.image_provider import ImageProvider, PlaceholderImageProvider
from core.scene_splitter import RuleBasedSceneSplitter
from core.schema import AudioAsset, ClipAsset, ImageAsset, ProduceResult, VideoPlan, to_dict, video_plan_from_dict
from core.tts import EdgeTTSProvider, TTSProvider
from core.video_renderer import VideoRenderer
from utils.file_utils import read_json, read_text, write_json
from utils.media_utils import make_job_id, scene_filename
from utils.subtitle_utils import write_srt

logger = logging.getLogger(__name__)

PRODUCE_STEPS = ("all", "plan", "tts", "images", "clips", "subtitles", "compose")


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
        script_path: str | None = None,
        *,
        output_path: str | None = None,
        title: str | None = None,
        style: str = "clean",
        width: int | None = None,
        height: int | None = None,
        fps: int | None = None,
        use_tts: bool = False,
        reuse_assets: bool = False,
        job_id: str | None = None,
        from_plan: str | None = None,
        step: str = "all",
        force: bool = False,
    ) -> ProduceResult:
        """从文案文件生成视频。"""
        if step not in PRODUCE_STEPS:
            raise ValueError(f"Unknown produce step: {step}. Available: {PRODUCE_STEPS}")

        total_start = time.perf_counter()
        width = width or self._cfg.video_width
        height = height or self._cfg.video_height
        fps = fps or self._cfg.video_fps
        job_id = self._resolve_job_id(job_id=job_id, from_plan=from_plan)
        logger.info("=" * 50)
        logger.info(
            "ProducePipeline START: script=%s job_id=%s from_plan=%s step=%s size=%dx%d fps=%d tts=%s reuse_assets=%s force=%s",
            script_path, job_id, from_plan, step, width, height, fps, use_tts, reuse_assets, force,
        )

        plan_path = self._plan_path(job_id, from_plan=from_plan)
        plan = self._prepare_plan(
            script_path=script_path,
            plan_path=plan_path,
            title=title,
            style=style,
            width=width,
            height=height,
            fps=fps,
            step=step,
            force=force,
        )

        audio_asset = self._prepare_audio(
            plan=plan,
            job_id=job_id,
            plan_path=plan_path,
            use_tts=use_tts,
            step=step,
            force=force,
        )

        subtitle_path = self._cfg.output_subtitles_dir / f"{job_id}.srt"
        final_path = Path(output_path) if output_path else self._cfg.output_videos_dir / f"{job_id}.mp4"

        image_assets: list[ImageAsset] = []
        clip_assets: list[ClipAsset] = []
        video_path = str(final_path)

        if step == "plan":
            logger.info("Step 'plan' complete; downstream assets were not touched.")
        elif step == "tts":
            logger.info("Step 'tts' complete; run --step clips --force then --step compose --tts if durations changed.")
        elif step == "images":
            image_assets = self._prepare_images(plan, job_id, step=step, reuse_assets=reuse_assets, force=force)
            logger.info("Step 'images' complete; run --step clips next.")
        elif step == "clips":
            image_assets = self._prepare_images(plan, job_id, step="load", reuse_assets=True, force=False)
            clip_assets = self._prepare_clips(
                plan, image_assets, job_id, step=step, reuse_assets=reuse_assets, force=force,
            )
            logger.info("Step 'clips' complete; run --step compose next.")
        elif step == "subtitles":
            self._prepare_subtitles(plan, subtitle_path, step=step, force=force)
            logger.info("Step 'subtitles' complete.")
        elif step == "compose":
            clip_assets = self._prepare_clips(plan, [], job_id, step="load", reuse_assets=True, force=False)
            self._prepare_subtitles(plan, subtitle_path, step="load", force=False)
            video_path = self._prepare_video(
                plan, clip_assets, final_path, audio_asset, step=step, force=force,
            )
        else:
            image_assets = self._prepare_images(plan, job_id, step=step, reuse_assets=reuse_assets, force=force)
            clip_assets = self._prepare_clips(
                plan, image_assets, job_id, step=step, reuse_assets=reuse_assets, force=force,
            )
            self._prepare_subtitles(plan, subtitle_path, step=step, force=force)
            video_path = self._prepare_video(
                plan, clip_assets, final_path, audio_asset, step=step, force=force,
            )
        logger.info(
            "ProducePipeline DONE: step=%s final_video_touched=%s video=%s scenes=%d duration=%.1fs elapsed=%.1fs",
            step, step in {"all", "compose"}, video_path, len(plan.scenes),
            plan.total_duration, time.perf_counter() - total_start,
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

    def _resolve_job_id(self, *, job_id: str | None, from_plan: str | None) -> str:
        if job_id:
            return job_id
        if from_plan:
            return Path(from_plan).stem
        return make_job_id("video")

    def _plan_path(self, job_id: str, *, from_plan: str | None) -> Path:
        return Path(from_plan) if from_plan else self._cfg.output_plans_dir / f"{job_id}.json"

    def _prepare_plan(
        self,
        *,
        script_path: str | None,
        plan_path: Path,
        title: str | None,
        style: str,
        width: int,
        height: int,
        fps: int,
        step: str,
        force: bool,
    ) -> VideoPlan:
        should_create = step in {"all", "plan"} and (force or not plan_path.exists())
        if should_create:
            if not script_path:
                raise ValueError("--script is required when creating or forcing a video plan")
            step_start = time.perf_counter()
            logger.info("[1/7] Splitting script into scenes ...")
            script = read_text(script_path)
            plan = self._splitter.split(script, title=title, style=style, width=width, height=height, fps=fps)
            self._log_plan_summary(plan, step_start)
            self._save_plan(plan, plan_path)
            return plan

        if plan_path.exists():
            step_start = time.perf_counter()
            logger.info("[1/7] Loading existing video plan: %s", plan_path)
            plan = video_plan_from_dict(read_json(plan_path))
            logger.info(
                "      -> %d scenes, %.1fs (%.1fs)",
                len(plan.scenes), plan.total_duration, time.perf_counter() - step_start,
            )
            return plan

        if not script_path:
            raise FileNotFoundError(f"Video plan not found: {plan_path}. Provide --script or --from-plan.")

        step_start = time.perf_counter()
        logger.info("[1/7] Splitting script into scenes ...")
        script = read_text(script_path)
        plan = self._splitter.split(script, title=title, style=style, width=width, height=height, fps=fps)
        self._log_plan_summary(plan, step_start)
        self._save_plan(plan, plan_path)
        return plan

    def _prepare_audio(
        self,
        *,
        plan: VideoPlan,
        job_id: str,
        plan_path: Path,
        use_tts: bool,
        step: str,
        force: bool,
    ) -> AudioAsset | None:
        audio_path = self._audio_path(job_id)
        legacy_audio_path = self._legacy_audio_path(job_id)
        if not use_tts:
            logger.info("[2/7] Skipping TTS audio (--no-tts)")
            return None

        if step in {"all", "tts"}:
            if audio_path.exists() and not force:
                logger.info("[2/7] Reusing TTS audio: %s", audio_path)
                return AudioAsset(str(audio_path), duration=self._audio_duration(audio_path), provider="edge-tts", voice=self._cfg.tts_voice)
            if legacy_audio_path.exists() and not force:
                logger.info("[2/7] Reusing legacy TTS audio: %s", legacy_audio_path)
                return AudioAsset(
                    str(legacy_audio_path),
                    duration=self._audio_duration(legacy_audio_path),
                    provider="edge-tts",
                    voice=self._cfg.tts_voice,
                )

            logger.info("[2/7] Generating TTS audio ...")
            before_duration = plan.total_duration
            audio_asset = self._synthesize_audio(plan, job_id)
            if audio_asset.duration > 0 and plan.total_duration > 0:
                self._scale_scene_durations(plan, audio_asset.duration)
                self._save_plan(plan, plan_path)
                logger.info(
                    "      -> scaled scene durations: %.1fs -> %.1fs",
                    before_duration, plan.total_duration,
                )
                logger.warning(
                    "      TTS changed scene durations. Re-render clips before compose for accurate sync: --step clips --force"
                )
            return audio_asset

        if audio_path.exists():
            logger.info("[2/7] Loading existing TTS audio: %s", audio_path)
            return AudioAsset(str(audio_path), duration=self._audio_duration(audio_path), provider="edge-tts", voice=self._cfg.tts_voice)
        if legacy_audio_path.exists():
            logger.info("[2/7] Loading existing legacy TTS audio: %s", legacy_audio_path)
            return AudioAsset(
                str(legacy_audio_path),
                duration=self._audio_duration(legacy_audio_path),
                provider="edge-tts",
                voice=self._cfg.tts_voice,
            )

        if step == "compose":
            raise FileNotFoundError(f"TTS audio not found: {audio_path}. Run --step tts --tts first.")
        logger.info("[2/7] TTS audio not present; continuing without audio")
        return None

    def _prepare_images(
        self,
        plan: VideoPlan,
        job_id: str,
        *,
        step: str,
        reuse_assets: bool,
        force: bool,
    ) -> list[ImageAsset]:
        if step in {"all", "images"}:
            logger.info("[4/7] Generating images ...")
            return self._generate_images(plan, job_id, reuse_assets=reuse_assets, force=force)

        logger.info("[4/7] Loading existing images ...")
        return self._load_images(plan, job_id)

    def _prepare_clips(
        self,
        plan: VideoPlan,
        image_assets: list[ImageAsset],
        job_id: str,
        *,
        step: str,
        reuse_assets: bool,
        force: bool,
    ) -> list[ClipAsset]:
        if step in {"all", "clips"}:
            logger.info("[5/7] Rendering animated scene clips ...")
            return self._render_clips(plan, image_assets, job_id, reuse_assets=reuse_assets, force=force)

        logger.info("[5/7] Loading existing animated scene clips ...")
        return self._load_clips(plan, job_id)

    def _prepare_subtitles(self, plan: VideoPlan, subtitle_path: Path, *, step: str, force: bool) -> None:
        if step in {"all", "subtitles"} or force or not subtitle_path.exists():
            step_start = time.perf_counter()
            logger.info("[6/7] Writing subtitles ...")
            write_srt(plan, subtitle_path, max_chars=self._cfg.video_subtitle_max_chars)
            logger.info("      -> %s (%.1fs)", subtitle_path, time.perf_counter() - step_start)
        else:
            logger.info("[6/7] Reusing subtitles: %s", subtitle_path)

    def _prepare_video(
        self,
        plan: VideoPlan,
        clip_assets: list[ClipAsset],
        final_path: Path,
        audio_asset: AudioAsset | None,
        *,
        step: str,
        force: bool,
    ) -> str:
        if step in {"all", "compose"} or force or not final_path.exists():
            step_start = time.perf_counter()
            logger.info("[7/7] Composing final video ...")
            video_path = self._renderer.compose(plan, clip_assets, final_path, audio=audio_asset)
            logger.info("      -> %s (%.1fs)", video_path, time.perf_counter() - step_start)
            return video_path

        logger.info("[7/7] Reusing final video: %s", final_path)
        return str(final_path)

    def _synthesize_audio(self, plan: VideoPlan, job_id: str) -> AudioAsset:
        text = "\n".join(scene.narration for scene in plan.scenes)
        audio_path = self._audio_path(job_id)
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

    def _audio_path(self, job_id: str) -> Path:
        """TTS 音频放在最终视频同目录，方便检查和归档。"""
        return self._cfg.output_videos_dir / f"{job_id}.mp3"

    def _legacy_audio_path(self, job_id: str) -> Path:
        """兼容旧版本输出到 outputs/audio 的音频。"""
        return self._cfg.output_audio_dir / f"{job_id}.mp3"

    def _generate_images(self, plan: VideoPlan, job_id: str, *, reuse_assets: bool, force: bool) -> list[ImageAsset]:
        image_dir = self._cfg.output_images_dir / job_id
        assets = []
        start = time.perf_counter()
        for position, scene in enumerate(plan.scenes, start=1):
            image_path = image_dir / scene_filename(scene.index, ".png")
            if image_path.exists() and reuse_assets and not force:
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

    def _load_images(self, plan: VideoPlan, job_id: str) -> list[ImageAsset]:
        image_dir = self._cfg.output_images_dir / job_id
        assets = []
        for position, scene in enumerate(plan.scenes, start=1):
            image_path = image_dir / scene_filename(scene.index, ".png")
            if not image_path.exists():
                raise FileNotFoundError(
                    f"Image not found for scene {scene.index}: {image_path}. Run --step images first."
                )
            logger.info("      [%d/%d] image: %s", position, len(plan.scenes), image_path)
            assets.append(ImageAsset(scene.index, str(image_path), prompt=scene.image_prompt))
        return assets

    def _render_clips(
        self,
        plan: VideoPlan,
        image_assets: list[ImageAsset],
        job_id: str,
        *,
        reuse_assets: bool,
        force: bool,
    ) -> list[ClipAsset]:
        clip_dir = self._cfg.output_clips_dir / job_id
        assets = []
        images_by_scene = {asset.scene_index: asset for asset in image_assets}
        start = time.perf_counter()
        for position, scene in enumerate(plan.scenes, start=1):
            clip_path = clip_dir / scene_filename(scene.index, ".mp4")
            if clip_path.exists() and reuse_assets and not force:
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

    def _load_clips(self, plan: VideoPlan, job_id: str) -> list[ClipAsset]:
        clip_dir = self._cfg.output_clips_dir / job_id
        assets = []
        for position, scene in enumerate(plan.scenes, start=1):
            clip_path = clip_dir / scene_filename(scene.index, ".mp4")
            if not clip_path.exists():
                raise FileNotFoundError(
                    f"Clip not found for scene {scene.index}: {clip_path}. Run --step clips first."
                )
            logger.info("      [%d/%d] clip: %s", position, len(plan.scenes), clip_path)
            assets.append(ClipAsset(scene.index, str(clip_path), scene.duration))
        return assets

    def _scale_scene_durations(self, plan: VideoPlan, target_duration: float) -> None:
        factor = target_duration / plan.total_duration
        for scene in plan.scenes:
            scene.duration = round(max(1.0, scene.duration * factor), 2)

    def _save_plan(self, plan: VideoPlan, plan_path: Path) -> None:
        step_start = time.perf_counter()
        logger.info("[3/7] Saving video plan JSON ...")
        write_json(plan_path, to_dict(plan))
        logger.info("      -> %s (%.1fs)", plan_path, time.perf_counter() - step_start)

    def _log_plan_summary(self, plan: VideoPlan, step_start: float) -> None:
        logger.info(
            "      -> %d scenes, estimated %.1fs (%.1fs)",
            len(plan.scenes), plan.total_duration, time.perf_counter() - step_start,
        )
        for scene in plan.scenes:
            logger.info(
                "      scene %03d: %.1fs animation=%s subtitle=%s",
                scene.index, scene.duration, scene.animation, self._preview(scene.subtitle),
            )

    def _audio_duration(self, audio_path: Path) -> float:
        try:
            from moviepy import AudioFileClip
        except ImportError:
            try:
                from moviepy.editor import AudioFileClip
            except ImportError:
                return 0.0
        clip = AudioFileClip(str(audio_path))
        try:
            return float(clip.duration or 0.0)
        finally:
            clip.close()

    def _preview(self, text: str, limit: int = 48) -> str:
        text = " ".join(text.split())
        return text if len(text) <= limit else f"{text[:limit]}..."
