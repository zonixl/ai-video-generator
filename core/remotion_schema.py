"""Remotion 独立流程的数据结构。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal


ComponentType = Literal[
    "title", "card", "arrow", "badge", "text", "metric", "step", "stat_counter", "progress", "list", "quote",
    "bar_chart", "line_chart", "donut_chart", "comparison", "circular_progress", "highlight_text", "typewriter",
    "progress_steps", "notification", "background_pattern", "lower_third",
]
ComponentSlot = Literal["title", "left_top", "left_bottom", "right_top", "right_bottom", "center", "bottom", "caption"]
ComponentVariant = Literal["default", "primary", "success", "danger", "warning", "muted"]
MotionType = Literal["fade_in", "slide_in", "pop", "draw", "strike", "pulse", "none"]
IconName = Literal["sparkles", "brain", "workflow", "image", "video", "audio", "check", "x", "zap", "target", "layers", "code", "settings"]


@dataclass
class RemotionComponentSpec:
    id: str
    type: ComponentType
    slot: ComponentSlot
    text: str = ""
    variant: ComponentVariant = "default"
    motion: MotionType = "fade_in"
    icon: IconName | str = ""


@dataclass
class RemotionSceneSpec:
    scene_index: int
    duration: float
    template: Literal["basic_diagram"] = "basic_diagram"
    theme: Literal["warm_grid", "dark_grid", "clean"] = "warm_grid"
    headline: str = ""
    subtitle: str = ""
    components: list[RemotionComponentSpec] = field(default_factory=list)


@dataclass
class RemotionVideoSpec:
    title: str
    width: int
    height: int
    fps: int
    scenes: list[RemotionSceneSpec]

    @property
    def total_duration(self) -> float:
        return sum(scene.duration for scene in self.scenes)


@dataclass
class RemotionProduceResult:
    job_id: str
    input_path: str
    video_path: str
    rendered: bool


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


def component_from_dict(data: dict[str, Any], fallback_id: str) -> RemotionComponentSpec:
    return RemotionComponentSpec(
        id=str(data.get("id") or fallback_id),
        type=_choice(data.get("type"), {
            "title", "card", "arrow", "badge", "text", "metric", "step", "stat_counter", "progress", "list", "quote",
            "bar_chart", "line_chart", "donut_chart", "comparison", "circular_progress", "highlight_text", "typewriter",
            "progress_steps", "notification", "background_pattern", "lower_third",
        }, "card"),
        slot=_choice(data.get("slot"), {
            "title", "left_top", "left_bottom", "right_top", "right_bottom", "center", "bottom", "caption"
        }, "bottom"),
        text=str(data.get("text", "")),
        variant=_choice(data.get("variant"), {"default", "primary", "success", "danger", "warning", "muted"}, "default"),
        motion=_choice(data.get("motion"), {"fade_in", "slide_in", "pop", "draw", "strike", "pulse", "none"}, "fade_in"),
        icon=_choice(data.get("icon"), {
            "sparkles", "brain", "workflow", "image", "video", "audio", "check", "x", "zap", "target", "layers", "code", "settings"
        }, ""),
    )


def scene_from_dict(data: dict[str, Any], fallback_index: int) -> RemotionSceneSpec:
    components = [
        component_from_dict(item, fallback_id=f"scene{fallback_index}_component{index}")
        for index, item in enumerate(data.get("components", []), start=1)
        if isinstance(item, dict)
    ]
    return RemotionSceneSpec(
        scene_index=int(data.get("scene_index") or data.get("index") or fallback_index),
        duration=float(data.get("duration", 5.0)),
        template="basic_diagram",
        theme=_choice(data.get("theme"), {"warm_grid", "dark_grid", "clean"}, "warm_grid"),
        headline=str(data.get("headline") or data.get("title") or f"Scene {fallback_index}"),
        subtitle=str(data.get("subtitle", "")),
        components=components,
    )


def video_from_dict(data: dict[str, Any]) -> RemotionVideoSpec:
    return RemotionVideoSpec(
        title=str(data.get("title", "Remotion Video")),
        width=int(data.get("width", 1080)),
        height=int(data.get("height", 1920)),
        fps=int(data.get("fps", 30)),
        scenes=[
            scene_from_dict(item, fallback_index=index)
            for index, item in enumerate(data.get("scenes", []), start=1)
            if isinstance(item, dict)
        ],
    )


def _choice(value: Any, allowed: set[str], default: str):
    value = str(value or "")
    return value if value in allowed else default

