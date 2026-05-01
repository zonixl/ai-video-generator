"""DeepSeek 驱动的 Remotion 图示视频规划。"""

from __future__ import annotations

import json
import logging
import re

from core import prompts
from core.remotion_schema import (
    RemotionComponentSpec,
    RemotionSceneSpec,
    RemotionVideoSpec,
    scene_from_dict,
)
from core.scene_splitter import RuleBasedSceneSplitter

logger = logging.getLogger(__name__)


class RuleBasedRemotionPlanner:
    """不调用 LLM 的 Remotion 兜底规划器。"""

    def __init__(self, splitter: RuleBasedSceneSplitter | None = None):
        self._splitter = splitter or RuleBasedSceneSplitter()

    def plan(self, script: str, *, title: str | None, width: int, height: int, fps: int) -> RemotionVideoSpec:
        video_plan = self._splitter.split(script, title=title, width=width, height=height, fps=fps)
        scenes = []
        for scene in video_plan.scenes:
            scenes.append(
                RemotionSceneSpec(
                    scene_index=scene.index,
                    duration=scene.duration,
                    headline=video_plan.title if scene.index == 1 else f"要点 {scene.index}",
                    subtitle=scene.subtitle,
                    components=[
                        RemotionComponentSpec("main", "card", "left_top", scene.subtitle[:18], "primary", "pop"),
                        RemotionComponentSpec("arrow", "arrow", "center", "", "default", "draw"),
                        RemotionComponentSpec("result", "card", "right_top", "关键结论", "success", "pop"),
                        RemotionComponentSpec("badge", "badge", "bottom", "AI -> Remotion", "warning", "slide_in"),
                    ],
                )
            )
        return RemotionVideoSpec(video_plan.title, width, height, fps, scenes)


class AIRemotionPlanner:
    """逐 scene 调用 LLM，生成受控 Remotion 组件 JSON。"""

    def __init__(
        self,
        model_manager,
        *,
        instance_name: str = "remotion_designer",
        fallback: RuleBasedRemotionPlanner | None = None,
        splitter: RuleBasedSceneSplitter | None = None,
    ):
        self._mgr = model_manager
        self._instance_name = instance_name
        self._fallback = fallback or RuleBasedRemotionPlanner(splitter=splitter)
        self._splitter = splitter or RuleBasedSceneSplitter()

    def plan(self, script: str, *, title: str | None, width: int, height: int, fps: int) -> RemotionVideoSpec:
        base_plan = self._splitter.split(script, title=title, width=width, height=height, fps=fps)
        scenes: list[RemotionSceneSpec] = []
        for scene in base_plan.scenes:
            user_prompt = prompts.PLAN_REMOTION_SCENE.format(
                title=base_plan.title,
                width=width,
                height=height,
                fps=fps,
                index=scene.index,
                duration=scene.duration,
                subtitle=scene.subtitle,
                visual=scene.visual,
            )
            try:
                response = self._mgr.generate(
                    self._instance_name,
                    user_prompt,
                    system_prompt=prompts.SYSTEM_REMOTION_DESIGNER,
                )
                remotion_scene = scene_from_dict(json.loads(self._extract_json(response)), scene.index)
                remotion_scene.scene_index = scene.index
                remotion_scene.duration = scene.duration
                remotion_scene.subtitle = remotion_scene.subtitle or scene.subtitle
                scenes.append(remotion_scene)
            except Exception:
                logger.warning("AI Remotion planning failed for scene %03d; using fallback", scene.index, exc_info=True)
                fallback_video = self._fallback.plan(scene.subtitle, title=base_plan.title, width=width, height=height, fps=fps)
                fallback_scene = fallback_video.scenes[0]
                fallback_scene.scene_index = scene.index
                fallback_scene.duration = scene.duration
                fallback_scene.subtitle = scene.subtitle
                scenes.append(fallback_scene)

        return RemotionVideoSpec(base_plan.title, width, height, fps, scenes)

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            raise ValueError("No JSON object found in Remotion planner response")
        return text[start:end + 1]

