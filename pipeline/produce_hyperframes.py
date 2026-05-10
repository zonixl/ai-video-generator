"""Safe HyperFrames video production pipeline."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from core.hyperframes_agent import HyperframesVideoAgent
from core.hyperframes_renderer import HyperframesRenderer
from core.hyperframes_sandbox import HyperframesSandbox
from core.hyperframes_schema import HyperframesProduceResult, HyperframesVideoRequest, to_dict
from utils.file_utils import read_text, write_json
from utils.media_utils import make_job_id

logger = logging.getLogger(__name__)


class ProduceHyperframesPipeline:
    def __init__(
        self,
        config,
        *,
        agent: HyperframesVideoAgent | None = None,
        renderer: HyperframesRenderer | None = None,
        model_manager=None,
    ):
        self._cfg = config
        self._root_dir = config.output_videos_dir / "hyperframes"
        self._sandbox = HyperframesSandbox(self._root_dir)
        self._renderer = renderer or HyperframesRenderer()
        self._agent = agent or HyperframesVideoAgent(model_manager=model_manager)

    def run(
        self,
        script_path: str | None = None,
        *,
        script_text: str | None = None,
        job_id: str | None = None,
        output_path: str | None = None,
        title: str | None = None,
        duration: int = 15,
        ratio: str = "9:16",
        style: str = "tech_hud",
        fps: int | None = None,
        use_agents_sdk: bool = True,
        render: bool = True,
        preview: bool = False,
    ) -> HyperframesProduceResult:
        start = time.perf_counter()
        script = script_text if script_text is not None else read_text(script_path) if script_path else ""
        if not script.strip():
            raise ValueError("script_path or script_text is required")

        job_id = job_id or make_job_id(title or script[:24])
        job = self._sandbox.create_job(job_id)
        request = HyperframesVideoRequest(
            script=script,
            title=title or "",
            duration=max(5, min(30, int(duration))),
            ratio=_validate_ratio(ratio),
            style=_validate_style(style),
            fps=fps or self._cfg.video_fps,
            use_agents_sdk=use_agents_sdk,
            render=render,
        )
        write_json(job.logs_dir / "request.json", to_dict(request))

        logger.info("ProduceHyperframes START: job_id=%s ratio=%s duration=%ss style=%s", job_id, request.ratio, request.duration, request.style)
        plan, already_written = self._agent.generate(request, job=job, sandbox=self._sandbox, renderer=self._renderer)
        write_json(job.logs_dir / "agent_plan.json", to_dict(plan))
        if not already_written:
            self._sandbox.write_files(job, plan.files)

        logs: list[str] = [str(job.logs_dir / "request.json"), str(job.logs_dir / "agent_plan.json")]
        preview_path = ""
        output = Path(output_path).resolve() if output_path else job.artifacts_dir / f"{job_id}.mp4"

        if render:
            # lint 结果仅供参考，不阻断渲染
            try:
                self._renderer.lint(job)
                logs.append(str(job.logs_dir / "hyperframes.lint.log"))
            except Exception:
                logger.warning("HyperFrames lint had issues (non-fatal).", exc_info=True)
                logs.append(str(job.logs_dir / "hyperframes.lint.log"))
            try:
                if preview:
                    preview_output = self._renderer.render_preview(job, frame=int(request.fps * min(2, request.duration)))
                    preview_path = str(preview_output)
                    logs.append(str(job.logs_dir / "hyperframes.preview.log"))
                output = self._renderer.render_video(job, output)
                logs.append(str(job.logs_dir / "hyperframes.render.log"))
                rendered = True
            except Exception:
                logger.warning("HyperFrames render failed; generated files are preserved in workspace.", exc_info=True)
                rendered = False
        else:
            rendered = False

        logger.info("ProduceHyperframes DONE: job_id=%s rendered=%s elapsed=%.1fs", job_id, rendered, time.perf_counter() - start)
        return HyperframesProduceResult(
            job_id=job_id,
            workspace_path=str(job.workspace_dir),
            output_path=str(output),
            preview_path=preview_path,
            rendered=rendered,
            logs=logs,
        )


def _validate_ratio(value: str) -> str:
    if value not in {"9:16", "16:9", "1:1"}:
        raise ValueError("ratio must be one of: 9:16, 16:9, 1:1")
    return value


def _validate_style(value: str) -> str:
    if value not in {"tech_hud", "data_stream", "glassmorphism", "cyber_grid"}:
        raise ValueError("style must be one of: tech_hud, data_stream, glassmorphism, cyber_grid")
    return value
