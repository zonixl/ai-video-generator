"""Remotion 视觉审查结果与安全 patch。"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any


ALLOWED_LAYOUTS = {"auto", "two_column_compare", "vertical_flow", "center_focus", "top_title_bottom_chart", "timeline_vertical", "quote_focus"}
ALLOWED_THEMES = {"warm_grid", "dark_grid", "clean"}
ALLOWED_MOTIONS = {"fade_in", "slide_in", "pop", "draw", "strike", "pulse", "none"}
ALLOWED_VARIANTS = {"default", "primary", "success", "danger", "warning", "muted"}
ALLOWED_COMPONENT_TYPES = {
    "title", "card", "arrow", "badge", "text", "metric", "step", "stat_counter", "progress", "list", "quote",
    "bar_chart", "line_chart", "donut_chart", "comparison", "circular_progress", "highlight_text", "typewriter",
    "progress_steps", "notification", "background_pattern", "lower_third",
}


@dataclass
class ReviewIssue:
    type: str
    severity: str
    scene_index: int
    reason: str
    suggestion: str = ""


@dataclass
class ReviewPatch:
    scene_index: int
    layout: str | None = None
    theme: str | None = None
    remove_component_ids: list[str] = field(default_factory=list)
    replace_component_type: dict[str, str] = field(default_factory=dict)
    shorten_text: dict[str, str] = field(default_factory=dict)
    set_motion: dict[str, str] = field(default_factory=dict)
    set_variant: dict[str, str] = field(default_factory=dict)
    limit_components: int | None = None


@dataclass
class ReviewResult:
    passed: bool
    score: int
    issues: list[ReviewIssue] = field(default_factory=list)
    patches: list[ReviewPatch] = field(default_factory=list)
    raw: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pass"] = data.pop("passed")
        return data


def parse_review_result(text: str) -> ReviewResult:
    data = json.loads(_extract_json(text))
    return ReviewResult(
        passed=bool(data.get("pass", False)),
        score=int(data.get("score", 0)),
        issues=[_parse_issue(item) for item in data.get("issues", []) if isinstance(item, dict)],
        patches=[patch for item in data.get("patches", []) if isinstance(item, dict) for patch in [_parse_patch(item)] if patch],
        raw=text,
    )


def _parse_issue(data: dict[str, Any]) -> ReviewIssue:
    return ReviewIssue(
        type=str(data.get("type", "unknown")),
        severity=str(data.get("severity", "medium")),
        scene_index=int(data.get("scene_index", 1)),
        reason=str(data.get("reason", "")),
        suggestion=str(data.get("suggestion", "")),
    )


def _parse_patch(data: dict[str, Any]) -> ReviewPatch | None:
    scene_index = int(data.get("scene_index", 0) or 0)
    if scene_index <= 0:
        return None
    return ReviewPatch(
        scene_index=scene_index,
        layout=_allowed(data.get("layout"), ALLOWED_LAYOUTS),
        theme=_allowed(data.get("theme"), ALLOWED_THEMES),
        remove_component_ids=_string_list(data.get("remove_component_ids")),
        replace_component_type=_allowed_map(data.get("replace_component_type"), ALLOWED_COMPONENT_TYPES),
        shorten_text=_string_map(data.get("shorten_text")),
        set_motion=_allowed_map(data.get("set_motion"), ALLOWED_MOTIONS),
        set_variant=_allowed_map(data.get("set_variant"), ALLOWED_VARIANTS),
        limit_components=_limit(data.get("limit_components")),
    )


def _extract_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("No JSON object found in vision review response")
    return text[start:end + 1]


def _allowed(value: Any, allowed: set[str]) -> str | None:
    value = str(value or "")
    return value if value in allowed else None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _string_map(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items() if str(key)}


def _allowed_map(value: Any, allowed: set[str]) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items() if str(key) and str(item) in allowed}


def _limit(value: Any) -> int | None:
    if value is None:
        return None
    return max(1, min(4, int(value)))
