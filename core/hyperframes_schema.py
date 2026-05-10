"""Schemas for the HyperFrames agent video workflow."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal, Any


HyperframesRatio = Literal["9:16", "16:9", "1:1"]
HyperframesStyle = Literal["tech_hud", "data_stream", "glassmorphism", "cyber_grid"]


@dataclass
class HyperframesVideoRequest:
    script: str
    title: str = ""
    duration: int = 15
    ratio: HyperframesRatio = "9:16"
    style: HyperframesStyle = "tech_hud"
    fps: int = 30
    use_agents_sdk: bool = True
    render: bool = True


@dataclass
class HyperframesFile:
    path: str
    content: str


@dataclass
class HyperframesAgentPlan:
    files: list[HyperframesFile]
    notes: str = ""


@dataclass
class HyperframesJob:
    job_id: str
    root_dir: Path
    workspace_dir: Path
    artifacts_dir: Path
    previews_dir: Path
    logs_dir: Path


@dataclass
class HyperframesProduceResult:
    job_id: str
    workspace_path: str
    output_path: str
    rendered: bool
    preview_path: str = ""
    logs: list[str] = field(default_factory=list)


def to_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return to_dict(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return [to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    return value


def plan_from_dict(data: dict[str, Any]) -> HyperframesAgentPlan:
    files = []
    for index, item in enumerate(data.get("files", []), start=1):
        if not isinstance(item, dict):
            continue
        files.append(
            HyperframesFile(
                path=str(item.get("path") or f"file_{index}.txt"),
                content=str(item.get("content") or ""),
            )
        )
    return HyperframesAgentPlan(files=files, notes=str(data.get("notes", "")))
