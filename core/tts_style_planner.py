"""AI 为整篇文章生成统一的 TTS 朗读风格。"""

from __future__ import annotations

import logging
import re

from core import prompts

logger = logging.getLogger(__name__)

# 可选风格名称集合
VALID_STYLES = {
    "自信坚定", "温柔亲切", "娓娓道来", "严肃沉稳",
    "兴奋激动", "急促紧张", "低沉神秘", "叙事平缓",
}


class TTSStylePlanner:
    """根据文章全文，选择一种最适合的统一朗读风格。"""

    def __init__(self, model_manager, *, instance_name: str = "summarizer"):
        self._mgr = model_manager
        self._instance_name = instance_name

    def plan(self, full_text: str) -> str:
        """返回风格名称（如 '叙事平缓'）。"""
        truncated = full_text[:3000]
        prompt = prompts.PLAN_TTS_WHOLE_STYLE.format(text=truncated)
        response = self._mgr.generate(
            self._instance_name,
            prompt,
            system_prompt=prompts.SYSTEM_TTS_STYLE,
        )
        return self._parse(response)

    def _parse(self, text: str) -> str:
        text = text.strip()
        # 去掉可能的引号、标点
        text = re.sub(r'[「」""''。，、.!！]', '', text)
        # 尝试精确匹配
        for style in VALID_STYLES:
            if style in text:
                logger.info("TTS unified style selected: %s", style)
                return style
        logger.warning("Could not parse TTS style from: %s, falling back to 叙事平缓", text[:50])
        return "叙事平缓"
