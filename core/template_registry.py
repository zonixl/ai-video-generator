"""Remotion 模板注册表：定义所有可用模板及其属性。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TemplateInfo:
    """模板元信息。"""
    name: str
    description: str        # 给 AI 选择用的描述
    needs_image: bool       # 是否需要文生图
    category: str           # image / static
    image_size: str = ""    # 图片尺寸类型：full / card_portrait / card / ""


TEMPLATES: dict[str, TemplateInfo] = {
    "basic_diagram": TemplateInfo(
        name="basic_diagram",
        description="图示卡片动画：卡片、箭头、指标、图表等组件的入场动画，适合数据/流程/对比类内容",
        needs_image=False,
        category="static",
    ),
    "kinetic_text": TemplateInfo(
        name="kinetic_text",
        description="逐词灵动文字：文字逐词弹出、上浮、翻转消失，配合语音节奏，适合金句/观点/短文案",
        needs_image=False,
        category="static",
    ),
    "image_full": TemplateInfo(
        name="image_full",
        description="全屏背景图：AI生成图片铺满屏幕，标题居中大字叠加，底部字幕半透明条，适合风景/故事/宏大主题",
        needs_image=True,
        category="image",
        image_size="full",
    ),
    "image_elegant": TemplateInfo(
        name="image_elegant",
        description="雅致插画：暖色背景+渐变光晕装饰，上方居中圆角AI插画，下方排版文字，适合人文/哲理/情感类",
        needs_image=True,
        category="image",
        image_size="card_portrait",
    ),
    "image_card": TemplateInfo(
        name="image_card",
        description="信息卡片：背景渐变+几何装饰，中央卡片内含AI插画，标题在卡片上方，字幕在卡片下方，适合科普/知识/解读类",
        needs_image=True,
        category="image",
        image_size="card",
    ),
    "image_modern": TemplateInfo(
        name="image_modern",
        description="现代科技：深色背景+几何线条，中央半透明玻璃卡片内AI插画，标题在卡片上方，适合科技/商业/趋势类",
        needs_image=True,
        category="image",
        image_size="card",
    ),
    "image_neon": TemplateInfo(
        name="image_neon",
        description="霓虹赛博：暗色底+霓虹渐变光晕，上方AI插画，下方粗体大字+荧光色高亮，适合潮流/游戏/音乐/年轻化内容",
        needs_image=True,
        category="image",
        image_size="card",
    ),
}


def get_template(name: str) -> TemplateInfo:
    """获取模板信息，未知模板回退到 basic_diagram。"""
    return TEMPLATES.get(name, TEMPLATES["basic_diagram"])


def needs_image(template_name: str) -> bool:
    """判断模板是否需要文生图。"""
    return get_template(template_name).needs_image


def all_template_names() -> list[str]:
    """返回所有模板名称。"""
    return list(TEMPLATES.keys())


def image_templates() -> list[str]:
    """返回需要图片的模板名称。"""
    return [name for name, info in TEMPLATES.items() if info.needs_image]


def get_image_size(template_name: str) -> str:
    """获取模板的图片尺寸类型：full / card / 空字符串。"""
    return get_template(template_name).image_size


def static_templates() -> list[str]:
    """返回不需要图片的模板名称。"""
    return [name for name, info in TEMPLATES.items() if not info.needs_image]


def template_choices_for_prompt() -> str:
    """生成给 AI 选择模板的 prompt 文本。"""
    lines = []
    for name, info in TEMPLATES.items():
        img_tag = "[需配图]" if info.needs_image else "[纯文字]"
        lines.append(f"- {name} {img_tag}：{info.description}")
    return "\n".join(lines)
