"""规则版文案分镜拆分。"""

from __future__ import annotations

import re
import json

from core import prompts
from core.schema import Scene, VideoPlan


class RuleBasedSceneSplitter:
    """用简单规则把文案拆成短视频分镜。"""

    def __init__(
        self,
        min_scene_duration: float = 5.0,
        max_scene_duration: float = 8.0,
        chars_per_second: float = 4.5,
    ):
        self._min_duration = min_scene_duration
        self._max_duration = max_scene_duration
        self._chars_per_second = chars_per_second

    def split(
        self,
        script: str,
        *,
        title: str | None = None,
        style: str = "clean",
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
    ) -> VideoPlan:
        """把完整文案拆分为 VideoPlan。"""
        clean_script, extracted_title = self._clean_script(script)
        title = title or extracted_title or "短视频"
        sentences = self._split_sentences(clean_script)
        groups = self._group_sentences(sentences)
        scenes = [
            self._build_scene(index + 1, text, title, style)
            for index, text in enumerate(groups)
        ]
        if not scenes:
            scenes = [self._build_scene(1, clean_script or title, title, style)]
        return VideoPlan(
            title=title,
            script=clean_script,
            scenes=scenes,
            width=width,
            height=height,
            fps=fps,
            style=style,
        )

    def _clean_script(self, script: str) -> tuple[str, str | None]:
        lines = []
        title = None
        for raw_line in script.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#") and title is None:
                title = line.lstrip("#").strip()
                continue
            line = re.sub(r"^[-*+]\s+", "", line)
            line = re.sub(r"^\d+[.)、]\s*", "", line)
            lines.append(line)
        return "\n".join(lines).strip(), title

    def _split_sentences(self, text: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            return []
        parts = re.split(r"(?<=[。！？!?；;])\s*", normalized)
        sentences = [part.strip() for part in parts if part.strip()]
        return sentences or [normalized]

    def _group_sentences(self, sentences: list[str]) -> list[str]:
        groups = []
        current = []
        current_chars = 0
        target_chars = int(self._max_duration * self._chars_per_second)

        for sentence in sentences:
            sentence_chars = self._count_chars(sentence)
            if current and current_chars + sentence_chars > target_chars:
                groups.append("".join(current))
                current = [sentence]
                current_chars = sentence_chars
            else:
                current.append(sentence)
                current_chars += sentence_chars

        if current:
            groups.append("".join(current))
        return groups

    def _build_scene(self, index: int, text: str, title: str, style: str) -> Scene:
        text = text.strip()
        duration = self._estimate_duration(text)
        visual = self._build_visual(text, title)
        animation = self._pick_animation(index)
        return Scene(
            index=index,
            subtitle=text,
            narration=text,
            visual=visual,
            image_prompt=f"{visual}，{style} 风格，竖屏短视频画面，高清",
            duration=duration,
            animation=animation,
        )

    def _estimate_duration(self, text: str) -> float:
        duration = self._count_chars(text) / self._chars_per_second
        return round(min(max(duration, self._min_duration), self._max_duration), 2)

    def _count_chars(self, text: str) -> int:
        return len(re.findall(r"[\u4e00-\u9fff]", text)) + len(re.findall(r"[A-Za-z0-9]+", text))

    def _build_visual(self, text: str, title: str) -> str:
        keywords = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", text)
        summary = "、".join(keywords[:4]) if keywords else title
        return f"围绕“{title}”的图文信息画面，重点呈现：{summary}"

    def _pick_animation(self, index: int) -> str:
        animations = ("zoom_in", "zoom_out", "pan_left", "pan_right", "fade")
        return animations[(index - 1) % len(animations)]


class AISceneSplitter:
    """用 LLM 生成更详细的视频分镜脚本。"""

    def __init__(
        self,
        model_manager,
        *,
        instance_name: str = "scene_planner",
        fallback: RuleBasedSceneSplitter | None = None,
        min_scene_duration: float = 5.0,
        max_scene_duration: float = 8.0,
    ):
        self._mgr = model_manager
        self._instance_name = instance_name
        self._fallback = fallback or RuleBasedSceneSplitter(
            min_scene_duration=min_scene_duration,
            max_scene_duration=max_scene_duration,
        )
        self._min_duration = min_scene_duration
        self._max_duration = max_scene_duration

    def split(
        self,
        script: str,
        *,
        title: str | None = None,
        style: str = "clean",
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
    ) -> VideoPlan:
        """用 AI 分镜；解析失败时回退到规则分镜。"""
        fallback_plan = self._fallback.split(
            script, title=title, style=style, width=width, height=height, fps=fps,
        )
        user_prompt = prompts.SPLIT_SCENES.format(
            title=title or fallback_plan.title,
            style=style,
            width=width,
            height=height,
            fps=fps,
            min_duration=self._min_duration,
            max_duration=self._max_duration,
            script=fallback_plan.script or script,
        )
        try:
            response = self._mgr.generate(
                self._instance_name,
                user_prompt,
                system_prompt=prompts.SYSTEM_SCENE_PLANNER,
            )
            return self._parse_response(
                response,
                fallback_plan=fallback_plan,
                style=style,
                width=width,
                height=height,
                fps=fps,
            )
        except Exception:
            import logging

            logging.getLogger(__name__).warning("AI scene split failed; falling back to rule splitter", exc_info=True)
            return fallback_plan

    def _parse_response(
        self,
        response: str,
        *,
        fallback_plan: VideoPlan,
        style: str,
        width: int,
        height: int,
        fps: int,
    ) -> VideoPlan:
        data = json.loads(self._extract_json(response))
        character_desc = str(data.get("character_description", "")).strip()
        scenes_data = data.get("scenes", data if isinstance(data, list) else [])
        scenes = []
        for position, item in enumerate(scenes_data, start=1):
            subtitle = str(item.get("subtitle") or item.get("narration") or "").strip()
            if not subtitle:
                continue
            visual = str(item.get("visual") or item.get("画面描述") or subtitle).strip()
            image_prompt = str(item.get("image_prompt") or visual).strip()
            scenes.append(
                Scene(
                    index=int(item.get("index") or item.get("scene") or position),
                    subtitle=subtitle,
                    narration=str(item.get("narration") or subtitle).strip(),
                    visual=visual,
                    image_prompt=image_prompt,
                    duration=self._normalize_duration(item.get("duration")),
                    animation=self._fallback._pick_animation(position),
                )
            )

        if not scenes:
            return fallback_plan
        for index, scene in enumerate(scenes, start=1):
            scene.index = index
        return VideoPlan(
            title=str(data.get("title") or fallback_plan.title),
            script=fallback_plan.script,
            scenes=scenes,
            width=width,
            height=height,
            fps=fps,
            style=style,
            character_description=character_desc,
        )

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        first_obj = text.find("{")
        first_arr = text.find("[")
        starts = [idx for idx in (first_obj, first_arr) if idx >= 0]
        if not starts:
            raise ValueError("No JSON found in AI scene response")
        start = min(starts)
        end = max(text.rfind("}"), text.rfind("]"))
        if end < start:
            raise ValueError("Invalid JSON bounds in AI scene response")
        return text[start:end + 1]

    def _normalize_duration(self, value) -> float:
        try:
            duration = float(value)
        except (TypeError, ValueError):
            duration = (self._min_duration + self._max_duration) / 2
        return round(min(max(duration, self._min_duration), self._max_duration), 2)

