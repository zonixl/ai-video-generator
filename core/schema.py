"""视频生产链路的数据结构。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Scene:
    """单个视频分镜。"""

    index: int
    subtitle: str
    narration: str
    visual: str
    image_prompt: str
    duration: float
    animation: str = "zoom_in"
    animation_notes: str = ""
    animation_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoPlan:
    """从文案拆分出的结构化视频计划。"""

    title: str
    script: str
    scenes: list[Scene]
    width: int = 1080
    height: int = 1920
    fps: int = 30
    style: str = "clean"
    character_description: str = ""

    @property
    def total_duration(self) -> float:
        return sum(scene.duration for scene in self.scenes)


@dataclass
class ImageAsset:
    """分镜图片素材。"""

    scene_index: int
    path: str
    provider: str = "placeholder"
    prompt: str = ""


@dataclass
class AudioAsset:
    """配音素材。"""

    path: str
    duration: float
    provider: str = "none"
    voice: str = ""


@dataclass
class ClipAsset:
    """渲染后的分镜视频片段。"""

    scene_index: int
    path: str
    duration: float


@dataclass
class ProduceResult:
    """文案到视频生产结果。"""

    job_id: str
    video_path: str
    plan_path: str
    subtitle_path: str
    image_paths: list[str] = field(default_factory=list)
    clip_paths: list[str] = field(default_factory=list)
    audio_path: str | None = None


def to_dict(value: Any) -> Any:
    """递归转换 dataclass 和 Path，方便写入 JSON。"""
    if hasattr(value, "__dataclass_fields__"):
        return to_dict(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return [to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    return value


def scene_from_dict(data: dict[str, Any]) -> Scene:
    return Scene(
        index=int(data["index"]),
        subtitle=str(data["subtitle"]),
        narration=str(data.get("narration", data["subtitle"])),
        visual=str(data.get("visual", "")),
        image_prompt=str(data.get("image_prompt", "")),
        duration=float(data["duration"]),
        animation=str(data.get("animation", "zoom_in")),
        animation_notes=str(data.get("animation_notes", "")),
        animation_params=dict(data.get("animation_params", {})),
    )


def video_plan_from_dict(data: dict[str, Any]) -> VideoPlan:
    return VideoPlan(
        title=str(data["title"]),
        script=str(data.get("script", "")),
        scenes=[scene_from_dict(item) for item in data.get("scenes", [])],
        width=int(data.get("width", 1080)),
        height=int(data.get("height", 1920)),
        fps=int(data.get("fps", 30)),
        style=str(data.get("style", "clean")),
        character_description=str(data.get("character_description", "")),
    )

