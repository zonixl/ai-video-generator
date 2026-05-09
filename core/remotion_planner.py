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
from core.template_registry import all_template_names

logger = logging.getLogger(__name__)


class RuleBasedRemotionPlanner:
    """不调用 LLM 的 Remotion 兜底规划器。"""

    def __init__(self, splitter: RuleBasedSceneSplitter | None = None):
        self._splitter = splitter or RuleBasedSceneSplitter()

    def plan(self, script: str, *, title: str | None, width: int, height: int, fps: int, template: str | None = None) -> RemotionVideoSpec:
        video_plan = self._splitter.split(script, title=title, width=width, height=height, fps=fps)
        scenes = []
        for scene in video_plan.scenes:
            if template == "sketch_course":
                scenes.append(self._plan_sketch_course_scene(scene, video_plan.title))
                continue
            s = RemotionSceneSpec(
                scene_index=scene.index,
                duration=scene.duration,
                headline=video_plan.title if scene.index == 1 else f"要点 {scene.index}",
                subtitle=scene.subtitle,
                components=[
                    RemotionComponentSpec("main", "card", "left_top", scene.subtitle[:18], "primary", "pop", "brain"),
                    RemotionComponentSpec("result", "card", "right_top", "关键结论", "success", "pop", "check"),
                    RemotionComponentSpec("badge", "badge", "bottom", "AI -> Remotion", "warning", "slide_in", "workflow"),
                ],
            )
            if template:
                s.template = template
            scenes.append(s)
        return RemotionVideoSpec(video_plan.title, width, height, fps, scenes)

    def _plan_sketch_course_scene(self, scene, title: str) -> RemotionSceneSpec:
        text = scene.subtitle.strip()
        lowered = text.lower()
        keywords = self._sketch_keywords(text)

        if any(token in text for token in ("对比", "区别", "不是", "而是")) or " vs " in lowered:
            left = keywords[0] if keywords else "旧方案"
            right = keywords[1] if len(keywords) > 1 else "新方案"
            result = keywords[2] if len(keywords) > 2 else (scene.visual or text[:18] or "关键差异")
            return RemotionSceneSpec(
                scene_index=scene.index,
                duration=scene.duration,
                template="sketch_course",
                theme="warm_grid",
                layout="vs_compare",
                headline=title if scene.index == 1 else "关键对比",
                subtitle=scene.subtitle,
                visual=scene.visual,
                components=[
                    RemotionComponentSpec("left", "card", "left_top", left, "danger", "strike", "x"),
                    RemotionComponentSpec("right", "card", "right_top", right, "success", "pop", "check"),
                    RemotionComponentSpec("note", "text", "center", result, "default", "slide_in", ""),
                    RemotionComponentSpec("result", "card", "bottom", result, "warning", "pop", "sparkles"),
                    RemotionComponentSpec("chip1", "badge", "caption", "对比", "muted", "pop", ""),
                    RemotionComponentSpec("chip2", "badge", "caption", "结论", "muted", "pop", ""),
                ],
            )

        if any(token in text for token in ("步骤", "流程", "生成", "输入", "理解", "输出", "完成")):
            steps = (keywords + ["输入", "理解", "输出"])[:3]
            return RemotionSceneSpec(
                scene_index=scene.index,
                duration=scene.duration,
                template="sketch_course",
                theme="warm_grid",
                layout="three_step_flow",
                headline=title if scene.index == 1 else "自动化流程",
                subtitle=scene.subtitle,
                visual=scene.visual,
                components=[
                    RemotionComponentSpec("step1", "card", "left_top", steps[0], "default", "pop", "message"),
                    RemotionComponentSpec("step2", "card", "center", steps[1], "warning", "pop", "brain"),
                    RemotionComponentSpec("step3", "card", "right_top", steps[2], "success", "pop", "check"),
                    RemotionComponentSpec("tip1", "badge", "caption", "识别意图", "muted", "pop", "target"),
                    RemotionComponentSpec("tip2", "badge", "caption", "整理结构", "muted", "pop", "layers"),
                    RemotionComponentSpec("tip3", "badge", "caption", "落地结果", "muted", "pop", "sparkles"),
                ],
            )

        if any(token in text for token in ("四", "4", "几个", "核心", "分类", "能力")):
            items = (keywords + ["核心能力", "实战场景", "日常使用", "结果沉淀"])[:4]
            return RemotionSceneSpec(
                scene_index=scene.index,
                duration=scene.duration,
                template="sketch_course",
                theme="warm_grid",
                layout="icon_grid",
                headline=title if scene.index == 1 else "实战场景",
                subtitle=scene.subtitle,
                visual=scene.visual,
                components=[
                    RemotionComponentSpec("item1", "card", "left_top", items[0], "warning", "pop", "settings"),
                    RemotionComponentSpec("item2", "card", "right_top", items[1], "success", "pop", "sparkles"),
                    RemotionComponentSpec("item3", "card", "left_bottom", items[2], "primary", "pop", "workflow"),
                    RemotionComponentSpec("item4", "card", "right_bottom", items[3], "warning", "pop", "file_text"),
                    RemotionComponentSpec("badge", "badge", "bottom", scene.visual or "分类梳理", "warning", "draw", "sparkles"),
                ],
            )

        return RemotionSceneSpec(
            scene_index=scene.index,
            duration=scene.duration,
            template="sketch_course",
            theme="warm_grid",
            layout="statement_highlight",
            headline=title if scene.index == 1 else "核心结论",
            subtitle=scene.subtitle,
            visual=scene.visual,
            components=[
                RemotionComponentSpec("main", "card", "center", text[:24] or "关键结论", "warning", "pop", "sparkles"),
                RemotionComponentSpec("note1", "badge", "caption", "重点", "muted", "pop", "target"),
                RemotionComponentSpec("note2", "badge", "caption", "解释", "muted", "pop", "book"),
            ],
        )

    def _sketch_keywords(self, text: str) -> list[str]:
        parts = re.split(r"[，,。、；;：:\n|/]+|不是|而是|通过|然后|再|最后|和|与|\+|->|→", text)
        keywords: list[str] = []
        for part in parts:
            clean = part.strip(" “”“”'\"")
            if not clean or len(clean) < 2:
                continue
            if clean in {"如果", "这些", "一个", "这个", "就是", "不是", "通过"}:
                continue
            keywords.append(clean[:12])
            if len(keywords) >= 6:
                break
        return keywords


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

    def plan(self, script: str, *, title: str | None, width: int, height: int, fps: int, template: str | None = None) -> RemotionVideoSpec:
        base_plan = self._splitter.split(script, title=title, width=width, height=height, fps=fps)
        scenes: list[RemotionSceneSpec] = []

        # 用户指定了模板则强制使用，否则由 AI 决定（第一个 scene 决定后统一）
        valid_templates = all_template_names()
        if template and template not in valid_templates:
            logger.warning("Unknown template '%s', valid: %s. Falling back to AI decision.", template, valid_templates)
            template = None
        chosen_template: str | None = template
        if chosen_template:
            logger.info("Template forced by user: %s", chosen_template)

        for scene in base_plan.scenes:
            try:
                # --- Stage 1: 选模板（仅第一个 scene） ---
                if chosen_template is None:
                    select_prompt = prompts.SELECT_REMOTION_TEMPLATE.format(
                        subtitle=scene.subtitle,
                        visual=scene.visual or "",
                    )
                    resp = self._mgr.generate(
                        self._instance_name,
                        select_prompt,
                        system_prompt=prompts.SYSTEM_REMOTION_DESIGNER,
                    )
                    chosen_template = self._parse_template(resp)
                    logger.info("Video template chosen: %s (from scene %03d)", chosen_template, scene.index)

                # --- Stage 2: 按模板类型生成 ---
                if chosen_template == "kinetic_text":
                    # kinetic 只输出骨架，实际动画由 kinetic_planner 填充
                    remotion_scene = self._build_kinetic_stub(scene, chosen_template)
                elif chosen_template.startswith("image_"):
                    prompt = prompts.PLAN_REMOTION_IMAGE.format(
                        index=scene.index,
                        duration=scene.duration,
                        subtitle=scene.subtitle,
                    )
                    resp = self._mgr.generate(
                        self._instance_name,
                        prompt,
                        system_prompt=prompts.SYSTEM_REMOTION_DESIGNER,
                    )
                    data = json.loads(self._extract_json(resp))
                    data["template"] = chosen_template
                    remotion_scene = scene_from_dict(data, scene.index)
                elif chosen_template == "sketch_course":
                    prompt = prompts.PLAN_REMOTION_SKETCH_COURSE.format(
                        index=scene.index,
                        duration=scene.duration,
                        subtitle=scene.subtitle,
                    )
                    resp = self._mgr.generate(
                        self._instance_name,
                        prompt,
                        system_prompt=prompts.SYSTEM_REMOTION_DESIGNER,
                    )
                    data = json.loads(self._extract_json(resp))
                    data["template"] = chosen_template
                    remotion_scene = scene_from_dict(data, scene.index)
                else:  # basic_diagram
                    prompt = prompts.PLAN_REMOTION_COMPONENTS.format(
                        index=scene.index,
                        duration=scene.duration,
                        subtitle=scene.subtitle,
                    )
                    resp = self._mgr.generate(
                        self._instance_name,
                        prompt,
                        system_prompt=prompts.SYSTEM_REMOTION_DESIGNER,
                    )
                    data = json.loads(self._extract_json(resp))
                    data["template"] = chosen_template
                    remotion_scene = scene_from_dict(data, scene.index)

                remotion_scene.scene_index = scene.index
                remotion_scene.duration = scene.duration
                remotion_scene.subtitle = remotion_scene.subtitle or scene.subtitle
                remotion_scene.visual = remotion_scene.visual or scene.visual
                remotion_scene.template = chosen_template
                scenes.append(remotion_scene)

            except Exception:
                logger.warning("AI Remotion planning failed for scene %03d; using fallback", scene.index, exc_info=True)
                fallback_video = self._fallback.plan(
                    scene.subtitle,
                    title=base_plan.title,
                    width=width,
                    height=height,
                    fps=fps,
                    template=chosen_template,
                )
                fallback_scene = fallback_video.scenes[0]
                fallback_scene.scene_index = scene.index
                fallback_scene.duration = scene.duration
                fallback_scene.subtitle = scene.subtitle
                if chosen_template:
                    fallback_scene.template = chosen_template
                scenes.append(fallback_scene)

        return RemotionVideoSpec(base_plan.title, width, height, fps, scenes)

    def _parse_template(self, text: str) -> str:
        """从 AI 响应中提取模板名。"""
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            raise ValueError("No JSON object found in template selection response")
        data = json.loads(text[start:end + 1])
        template = data.get("template", "basic_diagram")
        if template not in set(all_template_names()):
            logger.warning("AI selected unknown template '%s', falling back to basic_diagram", template)
            return "basic_diagram"
        return template

    def _build_kinetic_stub(self, scene, template: str) -> RemotionSceneSpec:
        """kinetic_text 模板的骨架，实际动画由 kinetic_planner 填充。"""
        return RemotionSceneSpec(
            scene_index=scene.index,
            duration=scene.duration,
            template=template,
            subtitle=scene.subtitle,
        )

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            raise ValueError("No JSON object found in Remotion planner response")
        return text[start:end + 1]
