"""独立 Remotion 视频生产流程。"""

from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path

from core.remotion_planner import RuleBasedRemotionPlanner
from core.remotion_refiner import RemotionRefiner
from core.remotion_renderer import RemotionRenderer
from core.remotion_schema import RemotionProduceResult, RemotionVideoSpec, to_dict, video_from_dict
from core.template_registry import needs_image
from core.tts import EdgeTTSProvider, _audio_duration
from utils.file_utils import read_json, read_text, write_json
from utils.media_utils import make_job_id

logger = logging.getLogger(__name__)

REMOTION_STEPS = ("all", "plan", "tts", "kinetic", "image", "refine", "render")


class ProduceRemotionPipeline:
    """文案 -> Remotion JSON -> TTS -> Refine -> Remotion 视频。"""

    def __init__(
        self,
        config,
        *,
        planner=None,
        renderer: RemotionRenderer | None = None,
        refiner: RemotionRefiner | None = None,
        tts_provider=None,
        kinetic_planner=None,
        image_provider=None,
    ):
        self._cfg = config
        self._planner = planner or RuleBasedRemotionPlanner()
        self._renderer = renderer or RemotionRenderer(config.remotion_project_dir)
        self._refiner = refiner
        self._tts_provider = tts_provider or EdgeTTSProvider()
        self._kinetic_planner = kinetic_planner
        self._image_provider = image_provider

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
        use_tts: bool = False,
        refine: bool = False,
        refine_rounds: int | None = None,
        review_only: bool = False,
    ) -> RemotionProduceResult:
        if step not in REMOTION_STEPS:
            raise ValueError(f"Unknown Remotion step: {step}. Available: {REMOTION_STEPS}")

        start = time.perf_counter()
        job_id = job_id or make_job_id("remotion")
        width = width or self._cfg.video_width
        height = height or self._cfg.video_height
        fps = fps or self._cfg.video_fps
        input_path = self._input_path(job_id)
        video_path = Path(output_path) if output_path else self._cfg.output_videos_dir / f"{job_id}.mp4"

        logger.info("=" * 50)
        logger.info(
            "ProduceRemotion START: script=%s job_id=%s step=%s size=%dx%d fps=%d tts=%s force=%s refine=%s",
            script_path, job_id, step, width, height, fps, use_tts, force, refine,
        )

        # ---- Step: plan ----
        spec = self._prepare_plan(
            script_path=script_path,
            input_path=input_path,
            title=title,
            width=width,
            height=height,
            fps=fps,
            step=step,
            force=force,
        )

        # ---- Step: tts ----
        if step in {"all", "tts"} and use_tts:
            logger.info("[2/5] Generating per-scene TTS audio ...")
            audio_asset = self._synthesize_audio(spec, job_id)
            # _synthesize_audio 内部已按每句话的实际音频时长设置 scene.duration
            self._copy_audio_for_remotion(audio_asset, job_id)
            spec.audio_src = f"{job_id}.mp3"
            write_json(input_path, to_dict(spec))
            logger.info("      -> audio_src saved: %s | total: %.1fs %d scenes",
                       spec.audio_src, spec.total_duration, len(spec.scenes))
        elif step == "tts" and not use_tts:
            logger.warning("Step 'tts' selected but --tts not enabled.")

        # ---- Step: kinetic_text ----
        if step in {"all", "kinetic"} and self._kinetic_planner:
            logger.info("[kinetic] Generating word-by-word animation config ...")
            for scene in spec.scenes:
                # 只为 kinetic_text 模板生成动画配置，不覆盖其他模板
                if scene.template not in ("kinetic_text", "basic_diagram"):
                    continue
                text = scene.subtitle.strip()
                if not text:
                    continue
                try:
                    config = self._kinetic_planner.plan(
                        text, scene.duration,
                        emotion=scene.tts_emotion or "", fps=spec.fps,
                    )
                    scene.kinetic_config = config
                    scene.template = "kinetic_text"
                    logger.info("      scene %03d: %d lines, %.1fs",
                                scene.scene_index, len(config.get("lines", [])), scene.duration)
                except Exception as exc:
                    logger.warning("Kinetic planning failed scene %03d: %s", scene.scene_index, exc)
            write_json(input_path, to_dict(spec))
            logger.info("      -> kinetic config saved for %d scenes", len(spec.scenes))

        # ---- Step: image generation ----
        if step in {"all", "image"} and self._image_provider:
            logger.info("[image] Generating scene images ...")
            public_dir = self._cfg.remotion_project_dir / "public"
            image_dir = public_dir / f"{job_id}_images"
            image_dir.mkdir(parents=True, exist_ok=True)
            for scene in spec.scenes:
                if not needs_image(scene.template):
                    continue
                prompt = scene.visual or scene.subtitle
                if not prompt.strip():
                    logger.warning("      scene %03d: no visual/subtitle, skipping image", scene.scene_index)
                    continue
                try:
                    from core.schema import Scene
                    pseudo_scene = Scene(
                        index=scene.scene_index,
                        duration=scene.duration,
                        subtitle=scene.subtitle,
                        visual=scene.visual or scene.subtitle,
                        image_prompt=prompt,
                    )
                    asset = self._image_provider.generate(
                        pseudo_scene, image_dir,
                        width=spec.width, height=spec.height,
                    )
                    # image_url 是相对于 remotion/public 的路径
                    scene.image_url = f"{job_id}_images/{Path(asset.path).name}"
                    logger.info("      scene %03d: %s", scene.scene_index, scene.image_url)
                except Exception as exc:
                    logger.warning("      scene %03d image FAILED: %s", scene.scene_index, exc)
            write_json(input_path, to_dict(spec))
            logger.info("      -> images saved for %d scenes", len(spec.scenes))

        # ---- Step: refine ----
        if step in {"all", "refine"} and (refine or step == "refine" or self._cfg.remotion_refine_enabled):
            if not self._refiner:
                raise RuntimeError("Remotion refiner is not configured")
            logger.info("[%s] Refining Remotion input with vision review ...",
                        "3/5" if (step == "all" and use_tts) else "2/4")
            try:
                self._refiner.refine(
                    input_path=input_path,
                    job_id=job_id,
                    max_rounds=refine_rounds or self._cfg.remotion_refine_rounds,
                    review_only=review_only,
                )
                spec = video_from_dict(read_json(input_path))
            except Exception as exc:
                logger.warning("Review step failed (skipped): %s", exc)
                logger.info("Continuing to render with current input ...")
        elif step == "refine":
            logger.info("Step 'refine' skipped because refine is disabled.")

        # ---- Step: render ----
        rendered = False
        if step in {"all", "render"}:
            step_label = "4/5" if (step == "all" and use_tts) else ("3/4" if (step == "all" and (refine or self._cfg.remotion_refine_enabled)) else "2/3") if step == "all" else "1/1"
            # Simplify the label logic
            logger.info("[render] Rendering Remotion video ...")
            self._renderer.render(input_path, video_path)
            rendered = True
        elif step == "refine":
            logger.info("Step 'refine' complete; final render was not touched.")
        elif step == "tts":
            logger.info("Step 'tts' complete; scene durations synced to audio.")
        elif step == "kinetic":
            logger.info("Step 'kinetic' complete; word animation configs generated.")
        else:
            logger.info("Step 'plan' complete; Remotion render was not touched.")

        logger.info(
            "ProduceRemotion DONE: job_id=%s input=%s video=%s scenes=%d rendered=%s elapsed=%.1fs",
            job_id, input_path, video_path, len(spec.scenes), rendered, time.perf_counter() - start,
        )
        return RemotionProduceResult(
            job_id=job_id,
            input_path=str(input_path),
            video_path=str(video_path),
            rendered=rendered,
        )

    # ---- plan ----

    def _prepare_plan(
        self,
        *,
        script_path: str | None,
        input_path: Path,
        title: str | None,
        width: int,
        height: int,
        fps: int,
        step: str,
        force: bool,
    ) -> RemotionVideoSpec:
        if input_path.exists() and not force:
            logger.info("[1/*] Loading existing Remotion input: %s", input_path)
            return video_from_dict(read_json(input_path))
        if step in {"tts", "render", "refine"}:
            raise FileNotFoundError(f"Remotion input not found: {input_path}. Run remotion plan first.")
        if not script_path:
            raise ValueError("--script is required when creating Remotion input")

        logger.info("[1/*] Planning Remotion component video ...")
        script = read_text(script_path)
        spec = self._planner.plan(script, title=title, width=width, height=height, fps=fps)
        write_json(input_path, to_dict(spec))
        logger.info("      -> %s (%d scenes, %.1fs)", input_path, len(spec.scenes), spec.total_duration)
        return spec

    # ---- tts ----

    def _synthesize_audio(self, spec: RemotionVideoSpec, job_id: str):
        """逐 scene 合成独立 TTS 音频，精确匹配每句话的时长。"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        scene_dir = self._cfg.output_videos_dir / f"{job_id}_scenes"
        scene_dir.mkdir(parents=True, exist_ok=True)
        voice = self._cfg.tts_voice
        rate = self._cfg.tts_speed
        is_edge = (hasattr(self._tts_provider, 'provider_name') and
                   self._tts_provider.provider_name == 'edge-tts')

        # 准备每 scene 的 TTS 文本 + 情感
        tasks: list[tuple[int, str, str, Path]] = []  # (index, text, emotion, output_path)
        for scene in spec.scenes:
            text = scene.subtitle.strip()
            if not text:
                continue
            emotion = getattr(scene, 'tts_emotion', '') or ''
            path = scene_dir / f"scene_{scene.scene_index:03d}.mp3"
            tasks.append((scene.scene_index, text, emotion, path))

        done, failed = 0, 0

        if is_edge:
            # EdgeTTS 串行（asyncio.run 在线程中不可靠）
            for idx, text, emotion, path in tasks:
                try:
                    asset = self._tts_provider.synthesize(text, path, voice=voice, rate=rate, emotion=emotion)
                    for scene in spec.scenes:
                        if scene.scene_index == idx:
                            scene.duration = round(max(1.0, asset.duration), 2)
                            break
                    done += 1
                    logger.info("      scene %03d: %.1fs emotion=%s", idx, asset.duration, emotion or '-')
                except Exception as exc:
                    failed += 1
                    logger.error("      scene %03d TTS FAILED: %s", idx, exc)
        else:
            # 讯飞 API 并行（最多3并发）
            with ThreadPoolExecutor(max_workers=min(3, len(tasks))) as executor:
                futures = {
                    executor.submit(
                        self._tts_provider.synthesize, text, path, voice=voice, rate=rate, emotion=emotion
                    ): (idx, path)
                    for idx, text, emotion, path in tasks
                }
                for future in as_completed(futures):
                    idx, path = futures[future]
                    try:
                        asset = future.result()
                        for scene in spec.scenes:
                            if scene.scene_index == idx:
                                scene.duration = round(max(1.0, asset.duration), 2)
                                break
                        done += 1
                        logger.debug("      scene %03d: %.1fs", idx, asset.duration)
                    except Exception as exc:
                        failed += 1
                        logger.error("      scene %03d TTS FAILED: %s", idx, exc)

        if failed > 0:
            logger.warning("      %d/%d scene TTS tasks failed", failed, len(tasks))
        logger.info("      -> %d scene audio clips (%.1fs total)",
                    done, spec.total_duration)

        # 拼接所有 scene 音频为一个文件
        audio_path = self._audio_path(job_id)
        clip_paths = [path for _, _, _, path in tasks if path.exists()]
        if not clip_paths:
            raise RuntimeError(f"No scene audio clips generated (all {len(tasks)} tasks failed)")
        self._concat_audio_clips(clip_paths, audio_path)
        duration = _audio_duration(audio_path)
        logger.info("      -> concatenated audio %.1fs saved: %s", duration, audio_path)
        from core.schema import AudioAsset
        return AudioAsset(path=str(audio_path), duration=duration, provider="edge-tts" if is_edge else "iflytek", voice=voice)

    def _concat_audio_clips(self, clip_paths: list[Path], output_path: Path) -> None:
        """用 moviepy 拼接多个 MP3 音频片段。"""
        if len(clip_paths) == 1:
            shutil.copy2(clip_paths[0], output_path)
            return
        try:
            from moviepy import AudioFileClip, concatenate_audioclips
        except ImportError:
            from moviepy.editor import AudioFileClip, concatenate_audioclips

        clips = []
        for p in clip_paths:
            try:
                clip = AudioFileClip(str(p))
                if clip.duration and clip.duration > 0:
                    clips.append(clip)
            except Exception:
                pass
        if not clips:
            raise RuntimeError("No valid audio clips to concatenate")
        if len(clips) == 1:
            clips[0].write_audiofile(str(output_path), logger=None)
        else:
            final = concatenate_audioclips(clips)
            final.write_audiofile(str(output_path), logger=None)
        for clip in clips:
            clip.close()

    def _audio_path(self, job_id: str) -> Path:
        return self._cfg.output_videos_dir / f"{job_id}.mp3"

    def _copy_audio_for_remotion(self, audio_asset, job_id: str) -> Path:
        """复制音频到 Remotion public/ 目录，使 staticFile() 可引用。"""
        public_dir = self._cfg.remotion_project_dir / "public"
        public_dir.mkdir(parents=True, exist_ok=True)
        dest = public_dir / f"{job_id}.mp3"
        shutil.copy2(audio_asset.path, dest)
        logger.info("      -> audio copied to remotion public/: %s", dest.name)
        return dest

    def _input_path(self, job_id: str) -> Path:
        return self._cfg.output_remotion_dir / job_id / "input.json"
