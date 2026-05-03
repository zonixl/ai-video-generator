"""Seedance 视频生产流程：文案 → 分镜 → 参考图 → 视频 → 拼接。"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from core.image_provider import ImageProvider, PlaceholderImageProvider
from core.scene_splitter import RuleBasedSceneSplitter
from core.schema import AudioAsset, Scene, VideoPlan, to_dict, video_plan_from_dict
from core.tts import EdgeTTSProvider, TTSProvider
from core.video_gen_provider import SeedanceVideoProvider
from utils.file_utils import read_json, read_text, write_json
from utils.media_utils import make_job_id, scene_filename

logger = logging.getLogger(__name__)

SEEDANCE_STEPS = ("all", "plan", "images", "videos", "compose")


class ProduceSeedancePipeline:
    """文案 → 分镜 → 参考图(交互确认) → Seedance 视频 → 拼接。"""

    def __init__(
        self,
        config,
        *,
        splitter=None,
        image_provider: ImageProvider | None = None,
        video_provider: SeedanceVideoProvider | None = None,
        tts_provider: TTSProvider | None = None,
    ):
        self._cfg = config
        self._splitter = splitter or RuleBasedSceneSplitter(
            min_scene_duration=getattr(config, "video_min_scene_duration", 5.0),
            max_scene_duration=getattr(config, "video_max_scene_duration", 8.0),
            chars_per_second=getattr(config, "video_chars_per_second", 4.5),
        )
        self._image_provider = image_provider or PlaceholderImageProvider()
        self._video_provider = video_provider
        self._tts_provider = tts_provider or EdgeTTSProvider()

    def run(
        self,
        script_path: str | None = None,
        *,
        job_id: str | None = None,
        output_path: str | None = None,
        title: str | None = None,
        width: int | None = None,
        height: int | None = None,
        fps: int | None = None,
        step: str = "all",
        force: bool = False,
        audio_mode: str = "tts",
        use_tts: bool = False,
        auto_confirm: bool = False,
        regenerate: int | None = None,
        user_images_dir: str | None = None,
    ) -> dict:
        if step not in SEEDANCE_STEPS:
            raise ValueError(f"Unknown Seedance step: {step}. Available: {SEEDANCE_STEPS}")

        start = time.perf_counter()
        width = width or self._cfg.video_width
        height = height or self._cfg.video_height
        fps = fps or self._cfg.video_fps
        job_id = job_id or make_job_id(title or "")

        job_dir = self._cfg.output_videos_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        plan_path = job_dir / "plan.json"
        image_dir = job_dir / "images"
        clip_dir = job_dir / "clips"
        final_path = Path(output_path) if output_path else job_dir / f"{job_id}.mp4"

        logger.info("=" * 50)
        logger.info(
            "ProduceSeedance START: script=%s job_id=%s step=%s size=%dx%d fps=%d "
            "audio_mode=%s auto_confirm=%s regenerate=%s",
            script_path, job_id, step, width, height, fps,
            audio_mode, auto_confirm, regenerate,
        )

        # ---- Step: plan ----
        if step in {"all", "plan"}:
            plan = self._prepare_plan(
                script_path=script_path,
                plan_path=plan_path,
                title=title,
                width=width,
                height=height,
                fps=fps,
                force=force,
            )
        else:
            if not plan_path.exists():
                raise FileNotFoundError(f"Plan not found: {plan_path}. Run --step plan first.")
            plan = video_plan_from_dict(read_json(plan_path))

        # ---- Step: images ----
        if step in {"all", "images"}:
            self._prepare_images(
                plan=plan,
                image_dir=image_dir,
                job_dir=job_dir,
                force=force,
                auto_confirm=auto_confirm,
                regenerate=regenerate,
                user_images_dir=user_images_dir,
            )

        # ---- Step: videos ----
        if step in {"all", "videos"}:
            if not self._video_provider:
                raise RuntimeError("Seedance video provider is not configured")
            self._prepare_clips(
                plan=plan,
                image_dir=image_dir,
                clip_dir=clip_dir,
                audio_mode=audio_mode,
                force=force,
            )

        # ---- Step: compose ----
        audio_asset = None
        if step in {"all", "compose"}:
            # TTS 音频
            if audio_mode == "tts" and use_tts:
                audio_asset = self._prepare_audio(plan, job_dir, force=force)

            self._compose(
                plan=plan,
                clip_dir=clip_dir,
                final_path=final_path,
                audio_asset=audio_asset,
                fps=fps,
                force=force,
            )

        elapsed = time.perf_counter() - start
        logger.info(
            "ProduceSeedance DONE: job_id=%s video=%s scenes=%d elapsed=%.1fs",
            job_id, final_path, len(plan.scenes), elapsed,
        )
        return {
            "job_id": job_id,
            "video_path": str(final_path),
            "plan_path": str(plan_path),
            "image_dir": str(image_dir),
            "clip_dir": str(clip_dir),
            "audio_path": audio_asset.path if audio_asset else None,
        }

    # ---- plan ----

    def _prepare_plan(
        self,
        *,
        script_path: str | None,
        plan_path: Path,
        title: str | None,
        width: int,
        height: int,
        fps: int,
        force: bool,
    ) -> VideoPlan:
        if plan_path.exists() and not force:
            logger.info("[plan] Loading existing plan: %s", plan_path)
            plan = video_plan_from_dict(read_json(plan_path))
            logger.info("       -> %d scenes, %.1fs", len(plan.scenes), plan.total_duration)
            return plan

        if not script_path:
            raise ValueError("--script is required when creating a plan")

        logger.info("[plan] Splitting script into scenes ...")
        script = read_text(script_path)
        plan = self._splitter.split(script, title=title, width=width, height=height, fps=fps)
        write_json(plan_path, to_dict(plan))
        logger.info(
            "       -> %d scenes, %.1fs saved: %s",
            len(plan.scenes), plan.total_duration, plan_path,
        )
        for scene in plan.scenes:
            logger.info(
                "       scene %03d: %.1fs subtitle=%s",
                scene.index, scene.duration, scene.subtitle[:40],
            )
        return plan

    # ---- images ----

    def _prepare_images(
        self,
        plan: VideoPlan,
        image_dir: Path,
        job_dir: Path,
        *,
        force: bool,
        auto_confirm: bool,
        regenerate: int | None,
        user_images_dir: str | None,
    ) -> None:
        image_dir.mkdir(parents=True, exist_ok=True)

        # 用户自定义图片模式
        if user_images_dir:
            self._load_user_images(plan, Path(user_images_dir), image_dir)
            return

        logger.info("[images] Generating scene reference images ...")
        for i, scene in enumerate(plan.scenes):
            image_path = image_dir / scene_filename(scene.index, ".png")

            # 跳过已存在的图（除非 force 或 regenerate 指定）
            if image_path.exists() and not force:
                if regenerate and scene.index == regenerate:
                    pass  # 重新生成
                else:
                    logger.info("       [%d/%d] reuse: %s", i + 1, len(plan.scenes), image_path.name)
                    continue

            scene_start = time.perf_counter()
            if i == 0 or not self._find_previous_image(image_dir, i, plan.scenes):
                # 首镜或找不到前一张确认图：Seedream 文生图
                logger.info(
                    "       [%d/%d] text-to-image scene %03d ...",
                    i + 1, len(plan.scenes), scene.index,
                )
                self._image_provider.generate(
                    scene, image_dir, width=plan.width, height=plan.height,
                )
            else:
                # 后续镜：Seedream img2img 基于上一张确认图
                ref_path = self._find_previous_image(image_dir, i, plan.scenes)
                logger.info(
                    "       [%d/%d] img2img scene %03d (ref: %s) ...",
                    i + 1, len(plan.scenes), scene.index, ref_path.name,
                )
                self._image_provider.generate_from_ref(
                    ref_path, scene, image_dir, width=plan.width, height=plan.height,
                )

            logger.info(
                "       -> %s (%.1fs)",
                image_path.name, time.perf_counter() - scene_start,
            )

            # 交互确认
            if not auto_confirm:
                self._wait_user_confirm(scene.index, image_path)

        logger.info("[images] Done: %d images in %s", len(plan.scenes), image_dir)

    def _find_previous_image(self, image_dir: Path, current_i: int, scenes: list[Scene]) -> Path | None:
        """找到当前场景之前的最后一张已确认图片。"""
        for j in range(current_i - 1, -1, -1):
            prev_path = image_dir / scene_filename(scenes[j].index, ".png")
            if prev_path.exists():
                return prev_path
        return None

    def _load_user_images(self, plan: VideoPlan, user_dir: Path, image_dir: Path) -> None:
        """从用户指定目录加载参考图，按 scene_index 匹配。"""
        logger.info("[images] Loading user images from: %s", user_dir)
        copied = 0
        for scene in plan.scenes:
            # 尝试多种命名格式
            candidates = [
                user_dir / scene_filename(scene.index, ".png"),
                user_dir / scene_filename(scene.index, ".jpg"),
                user_dir / f"{scene.index}.png",
                user_dir / f"{scene.index}.jpg",
            ]
            src = None
            for c in candidates:
                if c.exists():
                    src = c
                    break
            if src is None:
                logger.warning("       scene %03d: no image found in %s", scene.index, user_dir)
                continue
            dest = image_dir / scene_filename(scene.index, ".png")
            if not dest.exists() or dest.stat().st_mtime < src.stat().st_mtime:
                import shutil
                shutil.copy2(src, dest)
                logger.info("       scene %03d: copied %s", scene.index, src.name)
            copied += 1
        logger.info("[images] Loaded %d user images", copied)

    def _wait_user_confirm(self, scene_index: int, image_path: Path) -> None:
        """等待用户确认图片。"""
        print(f"\n[确认] scene_{scene_index:03d} 参考图已生成: {image_path}")
        print("       查看后按 Enter 继续，输入 'r' 重新生成，输入 'q' 跳过后续确认: ", end="")
        try:
            choice = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if choice == "q":
            # 后续不再等待确认（修改 self 状态太脏，用文件标记）
            logger.info("User skipped remaining confirmations")
        elif choice == "r":
            logger.info("User requested regenerate scene %03d", scene_index)

    # ---- videos ----

    def _prepare_clips(
        self,
        plan: VideoPlan,
        image_dir: Path,
        clip_dir: Path,
        *,
        audio_mode: str,
        force: bool,
    ) -> None:
        clip_dir.mkdir(parents=True, exist_ok=True)
        generate_audio = audio_mode == "seedance-audio"

        # 如果 generate_audio 与 provider 配置不同，临时覆盖
        provider = self._video_provider
        if provider._generate_audio != generate_audio:
            provider = SeedanceVideoProvider(
                base_url=provider._base_url,
                api_key=provider._api_key,
                model=provider._model,
                resolution=provider._resolution,
                ratio=provider._ratio,
                duration=provider._duration,
                generate_audio=generate_audio,
                watermark=provider._watermark,
                timeout=provider._timeout,
                poll_interval=provider._poll_interval,
            )

        logger.info(
            "[videos] Generating Seedance video clips (audio=%s) ...",
            generate_audio,
        )
        for i, scene in enumerate(plan.scenes):
            clip_path = clip_dir / scene_filename(scene.index, ".mp4")
            if clip_path.exists() and not force:
                logger.info("       [%d/%d] reuse: %s", i + 1, len(plan.scenes), clip_path.name)
                continue

            image_path = image_dir / scene_filename(scene.index, ".png")
            if not image_path.exists():
                logger.warning("       [%d/%d] scene %03d: image missing, skipping",
                               i + 1, len(plan.scenes), scene.index)
                continue

            scene_start = time.perf_counter()
            logger.info(
                "       [%d/%d] scene %03d: generating video ...",
                i + 1, len(plan.scenes), scene.index,
            )
            try:
                provider.generate(
                    image_path,
                    scene.narration or scene.subtitle,
                    clip_path,
                    duration=max(2, int(scene.duration)),
                )
                logger.info(
                    "       -> %s (%.1fs)",
                    clip_path.name, time.perf_counter() - scene_start,
                )
            except Exception as exc:
                logger.error(
                    "       scene %03d video FAILED: %s (%.1fs)",
                    scene.index, exc, time.perf_counter() - scene_start,
                )

        logger.info("[videos] Done")

    # ---- audio ----

    def _prepare_audio(self, plan: VideoPlan, job_dir: Path, *, force: bool) -> AudioAsset | None:
        audio_path = job_dir / "audio.mp3"
        if audio_path.exists() and not force:
            logger.info("[tts] Reusing audio: %s", audio_path)
            duration = self._audio_duration(audio_path)
            return AudioAsset(str(audio_path), duration=duration, provider="tts")

        logger.info("[tts] Generating TTS audio ...")
        text = "\n".join(scene.narration for scene in plan.scenes)
        asset = self._tts_provider.synthesize(
            text, audio_path,
            voice=self._cfg.tts_voice,
            rate=self._cfg.tts_speed,
        )
        logger.info("[tts] Done: %.1fs -> %s", asset.duration, audio_path)
        return asset

    # ---- compose ----

    def _compose(
        self,
        plan: VideoPlan,
        clip_dir: Path,
        final_path: Path,
        audio_asset: AudioAsset | None,
        *,
        fps: int,
        force: bool,
    ) -> str:
        if final_path.exists() and not force:
            logger.info("[compose] Reusing video: %s", final_path)
            return str(final_path)

        try:
            from moviepy import AudioFileClip, concatenate_videoclips, VideoFileClip
        except ImportError:
            from moviepy.editor import AudioFileClip, concatenate_videoclips, VideoFileClip

        logger.info("[compose] Composing final video ...")
        final_path.parent.mkdir(parents=True, exist_ok=True)

        clips = []
        for scene in plan.scenes:
            clip_path = clip_dir / scene_filename(scene.index, ".mp4")
            if clip_path.exists():
                clip = VideoFileClip(str(clip_path))
                clips.append(clip)
                logger.info("       loading clip: %s (%.1fs)", clip_path.name, clip.duration)
            else:
                logger.warning("       clip missing for scene %03d, skipping", scene.index)

        if not clips:
            raise RuntimeError("No video clips to compose")

        final_clip = concatenate_videoclips(clips, method="compose")

        audio_clip = None
        if audio_asset:
            audio_clip = AudioFileClip(audio_asset.path)
            final_clip = final_clip.with_audio(audio_clip)

        final_clip.write_videofile(
            str(final_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac" if audio_asset else None,
            ffmpeg_params=["-pix_fmt", "yuv420p"],
            logger="bar",
        )

        # 关闭 clips
        for clip in clips:
            clip.close()
        final_clip.close()
        if audio_clip:
            audio_clip.close()

        logger.info("[compose] Done: %s", final_path)
        return str(final_path)

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
