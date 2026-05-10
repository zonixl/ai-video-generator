"""AI 驱动的逐词动态文字动画规划器。"""

from __future__ import annotations

import json
import logging
import re

from core import prompts

logger = logging.getLogger(__name__)


class KineticTextPlanner:
    """调用 AI 为每个 scene 生成逐词动画配置。"""

    MAX_RETRIES = 3

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
        last_err = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = self._mgr.generate(
                    self._instance_name,
                    prompt,
                    system_prompt=prompts.SYSTEM_KINETIC_PLANNER,
                )
                data = json.loads(self._extract_json(response))
                if attempt > 1:
                    logger.info("Kinetic planner succeeded on attempt %d", attempt)
                return data
            except Exception as e:
                last_err = e
                logger.warning("Kinetic planner attempt %d/%d failed: %s",
                               attempt, self.MAX_RETRIES, e)
        raise last_err

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        # 去掉 markdown 代码块
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        # 去掉 ``` 前面可能残留的说明文字（取最后一个 ``` 块）
        code_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text)
        if code_blocks:
            text = code_blocks[-1]

        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            raise ValueError("No JSON object found in kinetic planner response")
        return text[start:end + 1]
