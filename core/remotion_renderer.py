"""Python 到 Remotion 的渲染桥接。"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class RemotionRenderer:
    """调用 Remotion CLI 渲染视频。"""

    def __init__(self, project_dir: str | Path):
        self._project_dir = Path(project_dir)

    def render(self, input_path: str | Path, output_path: str | Path) -> str:
        input_path = Path(input_path).resolve()
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        log_path = output_path.with_suffix(".remotion.log")

        npx = shutil.which("npx") or shutil.which("npx.cmd") or "npx"
        command = [
            npx,
            "remotion",
            "render",
            "src/index.ts",
            "DiagramVideo",
            str(output_path),
            f"--props={input_path}",
        ]
        logger.info("Remotion render start: cwd=%s input=%s output=%s", self._project_dir, input_path, output_path)
        result = subprocess.run(
            command,
            cwd=self._project_dir,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        log_path.write_text(
            f"$ {' '.join(command)}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}",
            encoding="utf-8",
        )
        if result.returncode != 0:
            raise RuntimeError(f"Remotion render failed ({result.returncode}). See log: {log_path}")
        logger.info("Remotion render done: %s", output_path)
        return str(output_path)

