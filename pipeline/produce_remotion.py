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
from core.tts import EdgeTTSProvider
from utils.file_utils import read_json, read_text, write_json
from utils.media_utils import make_job_id

logger = logging.getLogger(__name__)

REMOTION_STEPS = ("all", "plan", "tts", "refine", "render")


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
    ):
        self._cfg = config
        self._planner = planner or RuleBasedRemotionPlanner()
        self._renderer = renderer or RemotionRenderer(config.remotion_project_dir)
        self._refiner = refiner
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
            logger.info("[2/5] Generating TTS audio ...")
            audio_asset = self._synthesize_audio(spec, job_id)
            spec = self._sync_durations(spec, audio_asset.duration, input_path)
            # 复制到 Remotion public/ 目录，使用相对文件名引用
            self._copy_audio_for_remotion(audio_asset, job_id)
            spec.audio_src = f"{job_id}.mp3"
            write_json(input_path, to_dict(spec))
            logger.info("      -> audio_src saved in spec: %s", spec.audio_src)
        elif step == "tts" and not use_tts:
            logger.warning("Step 'tts' selected but --tts not enabled.")

        # ---- Step: refine ----
        if step in {"all", "refine"} and (refine or step == "refine" or self._cfg.remotion_refine_enabled):
            if not self._refiner:
                raise RuntimeError("Remotion refiner is not configured")
            logger.info("[%s] Refining Remotion input with vision review ...",
                        "3/5" if (step == "all" and use_tts) else "2/4")
            self._refiner.refine(
                input_path=input_path,
                job_id=job_id,
                max_rounds=refine_rounds or self._cfg.remotion_refine_rounds,
                review_only=review_only,
            )
            spec = video_from_dict(read_json(input_path))
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
        """从 scene 的 headline+subtitle 拼接 TTS 文本并合成音频。"""
        text = "\n".join(
            (scene.headline + "。" + scene.subtitle).strip("。") + "。"
            for scene in spec.scenes
        )
        audio_path = self._audio_path(job_id)
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
        logger.info("      -> audio %.1fs saved: %s", asset.duration, asset.path)
        return asset

    def _sync_durations(self, spec: RemotionVideoSpec, audio_duration: float, input_path: Path) -> RemotionVideoSpec:
        """按实际音频时长等比缩放所有 scene 的 duration，解决音字不同步。"""
        if spec.total_duration <= 0 or audio_duration <= 0:
            return spec

        before = spec.total_duration
        factor = audio_duration / spec.total_duration
        for scene in spec.scenes:
            scene.duration = round(max(1.0, scene.duration * factor), 2)

        # 写回 input.json，后续步骤使用缩放后的时长
        write_json(input_path, to_dict(spec))
        logger.info(
            "      -> scaled scene durations: %.1fs -> %.1fs (factor=%.4f)",
            before, spec.total_duration, factor,
        )
        if spec.total_duration != audio_duration:
            logger.info("      -> final total: %.1fs (audio: %.1fs, diff: %.1fs)",
                       spec.total_duration, audio_duration, audio_duration - spec.total_duration)
        return spec

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
