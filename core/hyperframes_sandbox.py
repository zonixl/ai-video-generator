"""Job-scoped filesystem sandbox for HyperFrames generation."""

from __future__ import annotations

import json
from pathlib import Path

from core.hyperframes_guard import (
    HyperframesSecurityError,
    resolve_in_workspace,
    validate_file_batch,
    validate_relative_path,
)
from core.hyperframes_schema import HyperframesFile, HyperframesJob


class HyperframesSandbox:
    def __init__(self, root_dir: str | Path):
        self._root_dir = Path(root_dir).resolve()

    def create_job(self, job_id: str) -> HyperframesJob:
        safe_job_id = validate_job_id(job_id)
        root = (self._root_dir / safe_job_id).resolve()
        if self._root_dir != root and self._root_dir not in root.parents:
            raise HyperframesSecurityError(f"Job path escapes root: {job_id}")
        job = HyperframesJob(
            job_id=safe_job_id,
            root_dir=root,
            workspace_dir=root / "workspace",
            artifacts_dir=root / "artifacts",
            previews_dir=root / "previews",
            logs_dir=root / "logs",
        )
        for directory in (job.workspace_dir, job.artifacts_dir, job.previews_dir, job.logs_dir):
            directory.mkdir(parents=True, exist_ok=True)
        return job

    def write_file(self, job: HyperframesJob, path: str, content: str) -> Path:
        target = resolve_in_workspace(job.workspace_dir, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def write_files(self, job: HyperframesJob, files: list[HyperframesFile]) -> list[Path]:
        validate_file_batch([(item.path, item.content) for item in files])
        written = []
        for item in files:
            written.append(self.write_file(job, item.path, item.content))
        self.write_manifest(job, files)
        return written

    def read_file(self, job: HyperframesJob, path: str) -> str:
        target = resolve_in_workspace(job.workspace_dir, path)
        return target.read_text(encoding="utf-8")

    def list_files(self, job: HyperframesJob) -> list[str]:
        files = []
        for path in job.workspace_dir.rglob("*"):
            if path.is_file():
                files.append(path.relative_to(job.workspace_dir).as_posix())
        return sorted(files)

    def write_manifest(self, job: HyperframesJob, files: list[HyperframesFile]) -> Path:
        manifest = {
            "job_id": job.job_id,
            "files": [{"path": item.path, "bytes": len(item.content.encode("utf-8"))} for item in files],
        }
        target = job.logs_dir / "file_manifest.json"
        target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return target


def validate_job_id(job_id: str) -> str:
    if not job_id:
        raise HyperframesSecurityError("job_id is required")
    safe = "".join(ch for ch in job_id if ch.isalnum() or ch in "-_.")[:80]
    if not safe:
        raise HyperframesSecurityError(f"Invalid job_id: {job_id}")
    return safe
