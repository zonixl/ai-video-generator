"""独立 Remotion 视频生产流程。"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from core.remotion_planner import RuleBasedRemotionPlanner
from core.remotion_refiner import RemotionRefiner
from core.remotion_renderer import RemotionRenderer
from core.remotion_schema import RemotionProduceResult, RemotionVideoSpec, to_dict, video_from_dict
from utils.file_utils import read_json, read_text, write_json
from utils.media_utils import make_job_id

logger = logging.getLogger(__name__)

REMOTION_STEPS = ("all", "plan", "refine", "render")


class ProduceRemotionPipeline:
    """文案 -> Remotion JSON -> Remotion 视频。"""

    def __init__(
        self,
        config,
        *,
        planner=None,
        renderer: RemotionRenderer | None = None,
        refiner: RemotionRefiner | None = None,
    ):
        self._cfg = config
        self._planner = planner or RuleBasedRemotionPlanner()
        self._renderer = renderer or RemotionRenderer(config.remotion_project_dir)
        self._refiner = refiner

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
            "ProduceRemotion START: script=%s job_id=%s step=%s size=%dx%d fps=%d force=%s refine=%s",
            script_path, job_id, step, width, height, fps, force, refine,
        )

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

        if step in {"all", "refine"} and (refine or step == "refine" or self._cfg.remotion_refine_enabled):
            if not self._refiner:
                raise RuntimeError("Remotion refiner is not configured")
            logger.info("[2/3] Refining Remotion input with vision review ...")
            self._refiner.refine(
                input_path=input_path,
                job_id=job_id,
                max_rounds=refine_rounds or self._cfg.remotion_refine_rounds,
                review_only=review_only,
            )
            spec = video_from_dict(read_json(input_path))
        elif step == "refine":
            logger.info("Step 'refine' skipped because refine is disabled.")

        rendered = False
        if step in {"all", "render"}:
            logger.info("[3/3] Rendering Remotion video ...")
            self._renderer.render(input_path, video_path)
            rendered = True
        elif step == "refine":
            logger.info("Step 'refine' complete; final render was not touched.")
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
            logger.info("[1/2] Loading existing Remotion input: %s", input_path)
            return video_from_dict(read_json(input_path))
        if step == "render":
            raise FileNotFoundError(f"Remotion input not found: {input_path}. Run remotion-plan first.")
        if not script_path:
            raise ValueError("--script is required when creating Remotion input")

        logger.info("[1/2] Planning Remotion component video ...")
        script = read_text(script_path)
        spec = self._planner.plan(script, title=title, width=width, height=height, fps=fps)
        write_json(input_path, to_dict(spec))
        logger.info("      -> %s (%d scenes, %.1fs)", input_path, len(spec.scenes), spec.total_duration)
        return spec

    def _input_path(self, job_id: str) -> Path:
        return self._cfg.output_remotion_dir / job_id / "input.json"

