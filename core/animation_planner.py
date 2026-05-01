"""AI 动画编排。"""

from __future__ import annotations

import json
import logging
import re

from core import prompts
from core.schema import Scene, VideoPlan

logger = logging.getLogger(__name__)

ANIMATIONS = {"zoom_in", "zoom_out", "pan_left", "pan_right", "fade"}


class RuleBasedAnimationPlanner:
    """无需 LLM 的动画兜底编排。"""

    def plan(self, plan: VideoPlan) -> VideoPlan:
        animations = ("zoom_in", "zoom_out", "pan_left", "pan_right", "fade")
        for index, scene in enumerate(plan.scenes, start=1):
            if scene.animation not in ANIMATIONS:
                scene.animation = animations[(index - 1) % len(animations)]
            if not scene.animation_notes:
                scene.animation_notes = f"规则兜底动画：{scene.animation}"
            if not scene.animation_params:
                scene.animation_params = self._default_params(scene.animation)
        return plan

    def _default_params(self, animation: str) -> dict:
        if animation == "zoom_out":
            return {"start_scale": 1.08, "end_scale": 1.0, "easing": "linear"}
        if animation == "pan_left":
            return {"direction": "left", "offset_px": 40, "easing": "linear"}
        if animation == "pan_right":
            return {"direction": "right", "offset_px": 40, "easing": "linear"}
        if animation == "fade":
            return {"fade_in": 0.3, "fade_out": 0.3, "easing": "linear"}
        return {"start_scale": 1.0, "end_scale": 1.08, "easing": "linear"}


class AIAnimationPlanner:
    """逐个分镜调用 LLM 规划动画，避免一次生成过长导致不完整。"""

    def __init__(
        self,
        model_manager,
        *,
        instance_name: str = "animation_planner",
        fallback: RuleBasedAnimationPlanner | None = None,
    ):
        self._mgr = model_manager
        self._instance_name = instance_name
        self._fallback = fallback or RuleBasedAnimationPlanner()

    def plan(self, plan: VideoPlan) -> VideoPlan:
        for scene in plan.scenes:
            self._plan_one(plan, scene)
        return plan

    def _plan_one(self, plan: VideoPlan, scene: Scene) -> None:
        prompt = prompts.PLAN_SCENE_ANIMATION.format(
            title=plan.title,
            style=plan.style,
            width=plan.width,
            height=plan.height,
            fps=plan.fps,
            index=scene.index,
            duration=scene.duration,
            subtitle=scene.subtitle,
            visual=scene.visual,
            image_prompt=scene.image_prompt,
        )
        try:
            response = self._mgr.generate(
                self._instance_name,
                prompt,
                system_prompt=prompts.SYSTEM_ANIMATION_PLANNER,
            )
            data = json.loads(self._extract_json(response))
            animation = str(data.get("animation", scene.animation))
            if animation not in ANIMATIONS:
                raise ValueError(f"Unsupported animation: {animation}")
            scene.animation = animation
            scene.animation_notes = str(data.get("animation_notes", "")).strip()
            params = data.get("animation_params", {})
            scene.animation_params = params if isinstance(params, dict) else {}
        except Exception:
            logger.warning("AI animation planning failed for scene %03d; using fallback", scene.index, exc_info=True)
            self._fallback.plan(VideoPlan(plan.title, plan.script, [scene], plan.width, plan.height, plan.fps, plan.style))

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            raise ValueError("No JSON object found in animation response")
        return text[start:end + 1]

