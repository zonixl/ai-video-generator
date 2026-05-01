"""Prompt 模板集中管理。"""

# ============================================================
# 系统角色
# ============================================================
SYSTEM_SCRIPT_WRITER = (
    "你是一个专业的短视频文案写手。你的任务是：\n"
    "1. 根据给定的【话题】和【参考资料】生成短视频口播文案。\n"
    "2. 文案需要：开头3秒内抓人眼球、信息密度高、口语化、有节奏感。\n"
    "3. 字数控制在200-500字（方便1-3分钟口播）。\n"
    "4. 输出Markdown格式：先写标题(# 标题)，然后正文。\n"
    "5. 只用参考资料中的信息，不要编造。参考资料不足时，诚实说明。"
)

SYSTEM_POLISHER = (
    "你是一个专业的文案润色师。根据用户的反馈意见，对文案进行修改。\n"
    "如果有参考资料，可以适当引用来丰富内容，但不要偏离原文案主题。\n"
    "保持原文案的结构和核心信息，只针对用户提出的问题进行调整。\n"
    "输出修改后的完整文案。"
)

EXTRACT_KEYWORDS_PROMPT = """从以下文案中提取3-5个核心关键词，用于知识库检索。
只输出关键词，逗号分隔，不要加任何解释。

文案：
{text}

关键词："""

# ============================================================
# 用户 Prompt 模板
# ============================================================
GENERATE_SCRIPT = """## 话题
{topic}

## 风格要求
{style}

## 参考资料
{context}

请根据以上信息生成短视频口播文案。"""

POLISH_SCRIPT = """## 当前文案
{draft}

## 修改意见
{feedback}

请根据修改意见输出润色后的完整文案。"""

POLISH_SCRIPT_WITH_CONTEXT = """## 当前文案
{draft}

## 修改意见
{feedback}

## 知识库参考资料
{context}

请结合参考资料和修改意见，输出润色后的完整文案。"""

# ============================================================
# 摄入：转写文本重构
# ============================================================
SYSTEM_RESTRUCTURE = (
    "你是一个专业的文本编辑。你的任务是整理语音识别的原始转写文本。\n"
    "语音识别可能存在的错误：同音词替换、断句位置不对、口语化碎片、重复内容。\n"
    "按以下规则处理：\n"
    "1. 修正明显的语音识别错误（根据上下文推断正确的词）\n"
    "2. 补全不完整的句子使其通顺，但绝不添加原文中没有的事实\n"
    "3. 去除口语化的冗余：语气词（嗯、啊、那个）、重复的话、无意义的填充词\n"
    "4. 按主题/逻辑重组为层次清晰的段落，每段5-15句话\n"
    "5. 保留所有关键信息：人名、数字、日期、专有名词、核心观点\n"
    "6. 输出Markdown格式：用 ## 标题概括每段主题，正文是整理后的内容\n"
    "7. 不要添加'本段讲述了'、'这篇文章介绍了'这类元描述废话\n"
    "8. 不要添加原文中没有的知识、评价、总结"
)

RESTRUCTURE_TRANSCRIPT = """## 任务
请整理以下语音识别转写文本，修正错误，结构化输出。

## 要求
- 修正同音词、断句错误
- 去除口语冗余
- 按主题分段，每段带 ## 标题
- 只输出重构后的正文，不要加任何前言后语

## 原始转写文本
{transcript}

请输出重构后的文本："""

# ============================================================
# Phase 3-4：视频生产
# ============================================================
SYSTEM_SCENE_PLANNER = (
    "你是一个短视频导演和分镜脚本策划。你的任务是把口播文案拆成可执行的视频分镜。\n"
    "你必须输出严格 JSON，不要输出 Markdown 代码块，不要解释。\n"
    "分镜必须适合“图片 + 简单动画 + 口播字幕”的低成本视频生产方式。\n"
    "每个分镜都要有明确画面主体、构图、情绪、背景，避免空泛词。\n"
    "不要在这个阶段设计动画动作，动画会由后续独立任务完成。"
)

SPLIT_SCENES = """## 任务
把下面的短视频口播文案拆成详细分镜脚本，用于后续图片生成和简单动画合成。

## 视频参数
- 标题：{title}
- 风格：{style}
- 画幅：{width}x{height} 竖屏
- 帧率：{fps}
- 每个分镜建议时长：{min_duration}-{max_duration} 秒

## 分镜要求
1. 保持原文案信息顺序，不要编造新事实。
2. 每个分镜只承载一个清晰观点，字幕口语化、完整、可直接朗读。
3. `visual` 要描述画面：主体、背景、构图、色彩、情绪、镜头视角。
4. `image_prompt` 要适合图片生成模型，描述具体画面，不要写“文字、字幕、logo、水印”。
5. 不要设计动画动作，不要输出 animation 字段。
6. 总分镜数量根据文案自然决定，优先保证节奏清晰。
7. 输出必须是严格 JSON 对象，不要包含 ```json。

## 输出 JSON 格式
{{
  "title": "视频标题",
  "scenes": [
    {{
      "index": 1,
      "duration": 6.0,
      "subtitle": "这一镜的屏幕字幕和口播文本",
      "narration": "这一镜的口播文本，通常与 subtitle 一致",
      "visual": "详细画面描述",
      "image_prompt": "适合生图模型的详细中文提示词"
    }}
  ]
}}

## 文案
{script}

请只输出 JSON："""

IMAGE_PROMPT = """根据分镜描述生成图片生成 prompt：
分镜：{scene_description}
风格：{style}
要求：竖屏(1080x1920)，高清，适合短视频。不要文字、不要字幕、不要水印。
"""

SYSTEM_ANIMATION_PLANNER = (
    "你是一个短视频动画编排师。你只为单个分镜设计图片动画和渲染指令。\n"
    "当前系统只能执行受控的简单动画：zoom_in、zoom_out、pan_left、pan_right、fade。\n"
    "你必须输出严格 JSON，不要 Markdown，不要解释。"
)

PLAN_SCENE_ANIMATION = """## 任务
为下面这个单独分镜设计图片动画编排。注意：这不是分镜脚本任务，只负责动画。

## 可执行动画类型
- zoom_in：缓慢推进，适合强调主体、制造进入感。
- zoom_out：缓慢拉远，适合总结、展示全貌。
- pan_left：画面向左平移，适合流程、时间线、信息展开。
- pan_right：画面向右平移，适合从问题走向答案。
- fade：淡入淡出，适合转场、情绪缓和、抽象概念。

## 输出要求
1. `animation` 必须是上述五个值之一。
2. `animation_notes` 说明为什么这样编排，以及画面运动节奏。
3. `animation_params` 给出执行参数，用于后续渲染扩展；只输出数字或短字符串。
4. 不要修改字幕、口播、画面描述和图片 prompt。
5. 输出严格 JSON 对象。

## 输出 JSON 格式
{{
  "animation": "zoom_in",
  "animation_notes": "缓慢推进到主体，突出这一镜的核心观点。",
  "animation_params": {{
    "start_scale": 1.0,
    "end_scale": 1.08,
    "easing": "linear"
  }}
}}

## 视频信息
- 标题：{title}
- 风格：{style}
- 画幅：{width}x{height}
- FPS：{fps}

## 当前分镜
- 序号：{index}
- 时长：{duration}
- 字幕：{subtitle}
- 画面描述：{visual}
- 图片 prompt：{image_prompt}

请只输出 JSON："""

SYSTEM_REMOTION_DESIGNER = (
    "你是一个 Remotion 图示视频编排师。你只输出严格 JSON，不输出 Markdown，不解释。\n"
    "你不能设计人物镜头，不能输出 React/CSS/自由坐标。\n"
    "你只能使用 basic_diagram 模板，以及固定组件类型、slot、variant、motion。"
)

PLAN_REMOTION_SCENE = """## 任务
把下面这个短视频分镜转换成 Remotion 图示组件 JSON。只做一个 scene。

## 可用模板
- basic_diagram

## 可用组件 type
- title：标题文本
- card：信息卡片
- arrow：连接箭头
- badge：强调标签
- text：普通文字

## 可用 slot
- title
- left_top
- left_bottom
- right_top
- right_bottom
- center
- bottom
- caption

## 可用 variant
- default
- primary
- success
- danger
- warning
- muted

## 可用 motion
- fade_in
- slide_in
- pop
- draw
- strike
- pulse
- none

## 规则
1. 禁止人物镜头，禁止写实人物，优先用图示、卡片、箭头、标签。
2. 只能使用上面列出的 type、slot、variant、motion。
3. 组件数量控制在 3-6 个。
4. 文案要短，卡片文字尽量 2-10 个字。
5. 如果表达“替换、否定、废弃”，可用 danger + strike。
6. 如果表达“结果、目标、升级”，可用 success + pop。
7. 输出严格 JSON 对象，不要包含 ```json。

## 输出 JSON 格式
{{
  "scene_index": 1,
  "duration": 5.0,
  "template": "basic_diagram",
  "theme": "warm_grid",
  "headline": "这一镜标题",
  "subtitle": "这一镜字幕",
  "components": [
    {{"id": "c1", "type": "card", "slot": "left_top", "text": "问题", "variant": "danger", "motion": "strike"}},
    {{"id": "a1", "type": "arrow", "slot": "center", "text": "", "variant": "default", "motion": "draw"}},
    {{"id": "c2", "type": "card", "slot": "right_top", "text": "方案", "variant": "success", "motion": "pop"}}
  ]
}}

## 视频参数
- 标题：{title}
- 宽高：{width}x{height}
- FPS：{fps}

## 当前分镜
- 序号：{index}
- 时长：{duration}
- 字幕：{subtitle}
- 画面描述：{visual}

请只输出 JSON："""

OLD_SPLIT_SCENES = """将以下文案拆分为短视频分镜描述，每个分镜包含：画面描述、字幕文本、预估时长。

## 文案
{script}

## 输出格式
```json
[{{"scene": 1, "duration": 3, "visual": "画面描述", "subtitle": "字幕文本"}}, ...]
```"""

