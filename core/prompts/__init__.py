"""Prompt 模板集中管理。

所有提示词文本存放在同目录的 .txt 文件中，此处仅加载为模块变量。
新增/修改提示词只需编辑对应 .txt 文件，无需改动代码。
"""

from pathlib import Path

_PROMPT_DIR = Path(__file__).parent


def _load(name: str) -> str:
    """读取同目录下 {name}.txt 的内容，去除首尾空白。"""
    return (_PROMPT_DIR / f"{name}.txt").read_text(encoding="utf-8").strip()


# ============================================================
# 系统角色
# ============================================================
SYSTEM_SCRIPT_WRITER = _load("SYSTEM_SCRIPT_WRITER")
SYSTEM_POLISHER = _load("SYSTEM_POLISHER")
EXTRACT_KEYWORDS_PROMPT = _load("EXTRACT_KEYWORDS_PROMPT")

# ============================================================
# 用户 Prompt 模板
# ============================================================
GENERATE_SCRIPT = _load("GENERATE_SCRIPT")
POLISH_SCRIPT = _load("POLISH_SCRIPT")
POLISH_SCRIPT_WITH_CONTEXT = _load("POLISH_SCRIPT_WITH_CONTEXT")

# ============================================================
# 摄入：转写文本重构
# ============================================================
SYSTEM_RESTRUCTURE = _load("SYSTEM_RESTRUCTURE")
RESTRUCTURE_TRANSCRIPT = _load("RESTRUCTURE_TRANSCRIPT")

# ============================================================
# Phase 3-4：视频生产
# ============================================================
SYSTEM_SCENE_PLANNER = _load("SYSTEM_SCENE_PLANNER")
SPLIT_SCENES = _load("SPLIT_SCENES")
IMAGE_PROMPT = _load("IMAGE_PROMPT")
SYSTEM_ANIMATION_PLANNER = _load("SYSTEM_ANIMATION_PLANNER")
PLAN_SCENE_ANIMATION = _load("PLAN_SCENE_ANIMATION")

SYSTEM_REMOTION_DESIGNER = _load("SYSTEM_REMOTION_DESIGNER")
SELECT_REMOTION_TEMPLATE = _load("SELECT_REMOTION_TEMPLATE")
PLAN_REMOTION_COMPONENTS = _load("PLAN_REMOTION_COMPONENTS")
PLAN_REMOTION_SKETCH_COURSE = _load("PLAN_REMOTION_SKETCH_COURSE")
PLAN_REMOTION_IMAGE = _load("PLAN_REMOTION_IMAGE")
SYSTEM_REMOTION_REVIEWER = _load("SYSTEM_REMOTION_REVIEWER")
REVIEW_REMOTION_FRAMES = _load("REVIEW_REMOTION_FRAMES")
REVIEW_VIDEO_FRAMES = _load("REVIEW_VIDEO_FRAMES")
OLD_SPLIT_SCENES = _load("OLD_SPLIT_SCENES")

# ============================================================
# 逐词动态文字视频 (Kinetic Text)
# ============================================================
SYSTEM_KINETIC_PLANNER = _load("SYSTEM_KINETIC_PLANNER")
PLAN_KINETIC_TEXT = _load("PLAN_KINETIC_TEXT")

# ============================================================
# TTS 风格规划
# ============================================================
SYSTEM_TTS_STYLE = _load("SYSTEM_TTS_STYLE")
PLAN_TTS_WHOLE_STYLE = _load("PLAN_TTS_WHOLE_STYLE")

# ============================================================
# 图文推文生成
# ============================================================
SYSTEM_TWEET_WRITER = _load("SYSTEM_TWEET_WRITER")
GENERATE_TWEET = _load("GENERATE_TWEET")
POLISH_TWEET = _load("POLISH_TWEET")
PLAN_TWEET_IMAGES = _load("PLAN_TWEET_IMAGES")
