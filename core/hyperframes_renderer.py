"""Safe wrappers around the HyperFrames CLI."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from core.hyperframes_schema import HyperframesJob

logger = logging.getLogger(__name__)


class HyperframesRenderer:
    def __init__(self, *, timeout: int = 180):
        self._timeout = timeout

    def lint(self, job: HyperframesJob) -> Path:
        return self._run(job, ["hyperframes", "lint"], job.logs_dir / "hyperframes.lint.log")

    def render_preview(self, job: HyperframesJob, frame: int = 60) -> Path:
        output = job.previews_dir / f"frame_{int(frame):05d}.png"
        self._run(
            job,
            ["hyperframes", "still", "--frame", str(int(frame)), "--output", str(output)],
            job.logs_dir / "hyperframes.preview.log",
        )
        return output

    def render_video(self, job: HyperframesJob, output_path: str | Path | None = None) -> Path:
        output = Path(output_path).resolve() if output_path else job.artifacts_dir / f"{job.job_id}.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        self._run(
            job,
            ["hyperframes", "render", "--output", str(output)],
            job.logs_dir / "hyperframes.render.log",
        )
        return output

    def _run(self, job: HyperframesJob, args: list[str], log_path: Path) -> Path:
        npx = shutil.which("npx.cmd") or shutil.which("npx") or "npx"
        command = [npx, *args]
        logger.info("HyperFrames command: cwd=%s command=%s", job.workspace_dir, command)
        try:
            result = subprocess.run(
                command,
                cwd=job.workspace_dir,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired as exc:
            log_path.write_text(
                f"$ {' '.join(command)}\n\nTIMEOUT after {self._timeout}s\n{exc}",
                encoding="utf-8",
            )
            raise RuntimeError(f"HyperFrames command timed out. See log: {log_path}") from exc

        log_path.write_text(
            f"$ {' '.join(command)}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}",
            encoding="utf-8",
        )
        if result.returncode != 0:
            raise RuntimeError(f"HyperFrames command failed ({result.returncode}). See log: {log_path}")
        return log_path
