"""AI 驱动的逐词动态文字动画规划器。"""

from __future__ import annotations

import json
import logging
import re

from core import prompts

logger = logging.getLogger(__name__)


class KineticTextPlanner:
    """调用 AI 为每个 scene 生成逐词动画配置。"""

    def __init__(self, model_manager, *, instance_name: str = "kinetic_planner"):
        self._mgr = model_manager
        self._instance_name = instance_name

    def plan(self, subtitle: str, duration: float, *,
             emotion: str = "", fps: int = 30) -> dict:
        prompt = prompts.PLAN_KINETIC_TEXT.format(
            subtitle=subtitle,
            duration=duration,
            emotion=emotion or "叙事平缓",
            fps=fps,
        )
        response = self._mgr.generate(
            self._instance_name,
            prompt,
            system_prompt=prompts.SYSTEM_KINETIC_PLANNER,
        )
        return json.loads(self._extract_json(response))

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            raise ValueError("No JSON object found in kinetic planner response")
        return text[start:end + 1]
