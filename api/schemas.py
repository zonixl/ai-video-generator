"""Pydantic 请求/响应模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---- 请求 ----

class GenerateRequest(BaseModel):
    topic: str = Field(..., description="话题/关键词")
    style: str | None = Field("专业但不枯燥，适合短视频口播", description="文案风格")


class PolishRequest(BaseModel):
    input: str = Field(..., description="文案文件路径")
    feedback: str = Field(..., description="修改意见")


class ProduceRequest(BaseModel):
    script: str | None = Field(None, description="文案 Markdown/TXT 文件路径")
    job_id: str | None = Field(None, description="复用或继续某个任务")
    output: str | None = Field(None, description="输出 mp4 路径")
    title: str | None = Field(None, description="视频标题")
    style: str = Field("clean", description="画面风格描述")
    width: int | None = Field(None, description="视频宽度")
    height: int | None = Field(None, description="视频高度")
    fps: int | None = Field(None, description="视频帧率")
    step: str = Field("all", description="执行阶段")
    force: bool = Field(False, description="强制重做")
    use_tts: bool = Field(False, description="启用 TTS 配音")
    reuse_assets: bool = Field(False, description="复用已存在的图片和片段")
    from_plan: str | None = Field(None, description="从已有 video_plan.json 继续执行")


class ProduceRemotionRequest(BaseModel):
    script: str | None = Field(None, description="文案 Markdown/TXT 文件路径")
    job_id: str | None = Field(None, description="任务 ID")
    output: str | None = Field(None, description="输出 mp4 路径")
    title: str | None = Field(None, description="视频标题")
    width: int | None = Field(None, description="视频宽度")
    height: int | None = Field(None, description="视频高度")
    orientation: str | None = Field(None, description="预设画幅：portrait / landscape")
    fps: int | None = Field(None, description="视频帧率")
    step: str = Field("all", description="执行阶段")
    force: bool = Field(False, description="强制重做")
    use_tts: bool = Field(False, description="启用 TTS 配音")
    tts_mode: str | None = Field(None, description="TTS 模式: per_scene / whole_article")
    kinetic: bool = Field(False, description="启用逐词动态文字模式")
    template: str | None = Field(None, description="强制指定模板")
    refine: bool = Field(False, description="启用视觉自迭代")
    refine_rounds: int | None = Field(None, description="视觉自迭代最大轮数")
    review_only: bool = Field(False, description="只输出审查报告")


class ProduceSeedanceRequest(BaseModel):
    script: str | None = Field(None, description="文案 Markdown/TXT 文件路径")
    job_id: str | None = Field(None, description="任务 ID")
    output: str | None = Field(None, description="输出 mp4 路径")
    title: str | None = Field(None, description="视频标题")
    width: int | None = Field(None, description="视频宽度")
    height: int | None = Field(None, description="视频高度")
    fps: int | None = Field(None, description="视频帧率")
    step: str = Field("all", description="执行阶段")
    force: bool = Field(False, description="强制重做")
    audio_mode: str = Field("tts", description="音频模式：seedance-audio / tts / none")
    use_tts: bool = Field(False, description="启用 TTS 配音")
    auto_confirm: bool = Field(True, description="自动生成，跳过确认")
    regenerate: int | None = Field(None, description="重新生成指定 scene 的图片")
    user_images: str | None = Field(None, description="用户自定义图片目录")


class ProduceHyperframesRequest(BaseModel):
    script: str = Field(..., description="文案 Markdown/TXT 文件路径")
    job_id: str | None = Field(None, description="任务 ID")
    output: str | None = Field(None, description="输出 mp4 路径")
    title: str | None = Field(None, description="视频标题")
    duration: int = Field(15, description="视频时长（秒），5-30")
    ratio: str = Field("9:16", description="视频比例：9:16 / 16:9 / 1:1")
    style: str = Field("tech_hud", description="视觉风格：tech_hud / data_stream / glassmorphism / cyber_grid")
    fps: int | None = Field(None, description="视频帧率")
    preview: bool = Field(False, description="渲染前生成预览静帧")
    no_render: bool = Field(False, description="只生成文件，不渲染视频")
    no_agents_sdk: bool = Field(False, description="跳过 Agents SDK，使用本地生成")


class GenerateTweetRequest(BaseModel):
    topic: str | None = Field(None, description="话题/关键词（与 draft 二选一）")
    draft_path: str | None = Field(None, description="文章初稿文件路径（与 topic 二选一）")
    feedback: str | None = Field(None, description="润色意见（可选）")
    output: str | None = Field(None, description="输出 MD 路径（可选）")
    no_images: bool = Field(False, description="只生成文字，不生成配图")


class ReviewVideoRequest(BaseModel):
    video: str = Field(..., description="待审查 mp4 路径")
    job_id: str | None = Field(None, description="审查任务 ID")
    frames: int = Field(7, description="抽取关键帧数量")
    max_frame_width: int = Field(768, description="送审关键帧最大宽度")
    output_dir: str | None = Field(None, description="审查报告输出目录")
    reviewer_instance: str | None = Field(None, description="覆盖 reviewer instance")


class ClearRequest(BaseModel):
    confirm: bool = Field(False, description="确认清空")


class NukeRequest(BaseModel):
    confirm: bool = Field(False, description="确认清除所有数据")


class IngestTextRequest(BaseModel):
    text: str = Field("", description="直接输入的文本内容")
    name: str = Field("direct_input", description="来源名称")
    force: bool = Field(False, description="强制重新摄入")


class SaveScriptRequest(BaseModel):
    path: str = Field(..., description="文案文件路径")
    content: str = Field(..., description="文案内容")


class SaveTweetRequest(BaseModel):
    path: str = Field(..., description="推文文件路径")
    content: str = Field(..., description="推文内容")


# ---- 响应 ----

class JobResponse(BaseModel):
    id: str
    type: str
    status: str
    params: dict
    result: dict | None = None
    error: str | None = None
    created_at: float
    started_at: float | None = None
    finished_at: float | None = None


class GenerateResponse(BaseModel):
    script: str
    saved_path: str | None = None


class StatusResponse(BaseModel):
    collection: str
    doc_count: int
    instances: list[str]


class ScriptInfo(BaseModel):
    name: str
    path: str
    size: int
    modified: float


class VideoJobInfo(BaseModel):
    job_id: str
    path: str
    videos: list[str]
