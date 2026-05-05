"""FastAPI 应用入口：将 CLI 命令暴露为 REST API。"""

from __future__ import annotations

import argparse
import logging
import threading
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from api import db
from api.schemas import (
    ClearRequest,
    GenerateRequest,
    NukeRequest,
    PolishRequest,
    ProduceRemotionRequest,
    ProduceSeedanceRequest,
    ProduceRequest,
    ReviewVideoRequest,
)

logger = logging.getLogger("api")

app = FastAPI(
    title="AI 内容生产系统",
    description="短视频文案自动生成 & 视频制作 REST API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
#  工具函数
# ============================================================

def _make_args(**kwargs) -> argparse.Namespace:
    """构造 argparse.Namespace，填充默认 config/debug。"""
    kwargs.setdefault("config", None)
    kwargs.setdefault("debug", False)
    return argparse.Namespace(**{k: v for k, v in kwargs.items() if v is not None})


def _run_async(job_type: str, params: dict, fn, args: argparse.Namespace) -> dict:
    """创建异步任务并在后台线程执行。"""
    job_id = db.create_job(job_type, params)

    def _worker():
        db.update_job(job_id, status="running", started_at=time.time())
        try:
            fn(args)
            db.update_job(job_id, status="success", finished_at=time.time())
        except Exception as exc:
            logger.exception("Job %s failed", job_id)
            db.update_job(job_id, status="failed", error=str(exc), finished_at=time.time())

    threading.Thread(target=_worker, daemon=True).start()
    return {"job_id": job_id}


# ============================================================
#  同步接口
# ============================================================

@app.post("/api/generate", response_model=None, tags=["文案"])
def generate(req: GenerateRequest):
    """根据话题生成文案。"""
    from main import cmd_generate

    args = _make_args(topic=req.topic, style=req.style)
    try:
        # 捕获生成的文案：从 pipeline 返回值获取
        from main import build_generate_pipeline, Settings
        cfg = Settings()
        pipeline = build_generate_pipeline(cfg)
        script = pipeline.run(req.topic, style=req.style or "专业但不枯燥，适合短视频口播")
        return {"script": script}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.post("/api/polish", tags=["文案"])
def polish(req: PolishRequest):
    """润色已有文案。"""
    from main import cmd_polish

    args = _make_args(input=req.input, feedback=req.feedback)
    try:
        cmd_polish(args)
        return {"status": "ok", "message": "polish completed"}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/api/status", tags=["系统"])
def status():
    """查看知识库状态。"""
    from main import cmd_status, build_model_manager
    from config import Settings
    from core.vectordb import VectorStore

    cfg = Settings()
    vs = VectorStore(
        persist_dir=cfg.vectordb_persist_dir,
        collection_name=cfg.vectordb_collection_name,
    )
    model_mgr = build_model_manager(cfg)
    return {
        "collection": cfg.vectordb_collection_name,
        "doc_count": vs.count(),
        "instances": model_mgr.list_instances(),
    }


@app.post("/api/clear", tags=["系统"])
def clear(req: ClearRequest):
    """清空知识库。"""
    if not req.confirm:
        return JSONResponse(status_code=400, content={"error": "需要 confirm=true 确认"})

    args = _make_args(confirm=True)
    from main import cmd_clear
    try:
        cmd_clear(args)
        return {"status": "ok", "message": "knowledge base cleared"}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.post("/api/nuke", tags=["系统"])
def nuke(req: NukeRequest):
    """清除所有数据。"""
    if not req.confirm:
        return JSONResponse(status_code=400, content={"error": "需要 confirm=true 确认"})

    args = _make_args(confirm=True)
    from main import cmd_nuke
    try:
        cmd_nuke(args)
        return {"status": "ok", "message": "all data wiped"}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})


# ============================================================
#  异步接口
# ============================================================

@app.post("/api/ingest", tags=["摄入"])
async def ingest(
    file: UploadFile = File(..., description="音频文件"),
    force: bool = Query(False, description="强制重新摄入"),
):
    """上传音频文件并摄入知识库。"""
    from main import cmd_ingest

    upload_dir = Path("uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / (file.filename or "audio.mp3")
    file_path.write_bytes(await file.read())

    args = _make_args(input=str(file_path), force=force)
    return _run_async("ingest", {"input": str(file_path), "force": force}, cmd_ingest, args)


@app.post("/api/ingest-path", tags=["摄入"])
def ingest_path(input: str = Query(..., description="音频文件或文件夹路径"), force: bool = False):
    """通过路径摄入音频（不需要上传文件）。"""
    from main import cmd_ingest

    args = _make_args(input=input, force=force)
    return _run_async("ingest", {"input": input, "force": force}, cmd_ingest, args)


@app.post("/api/produce", tags=["视频生产"])
def produce(req: ProduceRequest):
    """根据文案生成图片动画视频。"""
    from main import cmd_produce

    args = _make_args(
        script=req.script, output=req.output, title=req.title, style=req.style,
        width=req.width, height=req.height, fps=req.fps,
        use_tts=req.use_tts, reuse_assets=req.reuse_assets,
        job_id=req.job_id, from_plan=req.from_plan,
        step=req.step, force=req.force,
    )
    return _run_async("produce", req.model_dump(), cmd_produce, args)


@app.post("/api/produce-remotion", tags=["视频生产"])
def produce_remotion(req: ProduceRemotionRequest):
    """根据文案生成 Remotion 图示视频。"""
    from main import cmd_produce_remotion

    args = _make_args(
        script=req.script, job_id=req.job_id, output=req.output, title=req.title,
        width=req.width, height=req.height, orientation=req.orientation,
        fps=req.fps, step=req.step, force=req.force,
        tts=req.use_tts, kinetic=req.kinetic, template=req.template,
        refine=req.refine, refine_rounds=req.refine_rounds,
        review_only=req.review_only,
    )
    return _run_async("produce-remotion", req.model_dump(), cmd_produce_remotion, args)


@app.post("/api/produce-seedance", tags=["视频生产"])
def produce_seedance(req: ProduceSeedanceRequest):
    """Seedance 图生视频。"""
    from main import cmd_produce_seedance

    args = _make_args(
        script=req.script, job_id=req.job_id, output=req.output, title=req.title,
        width=req.width, height=req.height, fps=req.fps,
        step=req.step, force=req.force,
        audio_mode=req.audio_mode, use_tts=req.use_tts,
        auto_confirm=req.auto_confirm, regenerate=req.regenerate,
        user_images=req.user_images,
    )
    return _run_async("produce-seedance", req.model_dump(), cmd_produce_seedance, args)


@app.post("/api/review-video", tags=["视频审查"])
def review_video(req: ReviewVideoRequest):
    """用多模态模型审查已生成视频。"""
    from main import cmd_review_video

    args = _make_args(
        video=req.video, job_id=req.job_id, frames=req.frames,
        max_frame_width=req.max_frame_width, output_dir=req.output_dir,
        reviewer_instance=req.reviewer_instance,
    )
    return _run_async("review-video", req.model_dump(), cmd_review_video, args)


# ============================================================
#  任务管理
# ============================================================

@app.get("/api/jobs", tags=["任务"])
def list_jobs(
    status: Optional[str] = Query(None, description="过滤状态：pending/running/success/failed"),
    limit: int = Query(50, le=200),
):
    """列出任务。"""
    return db.list_jobs(status=status, limit=limit)


@app.get("/api/jobs/{job_id}", tags=["任务"])
def get_job(job_id: str):
    """查询任务详情。"""
    job = db.get_job(job_id)
    if job is None:
        return JSONResponse(status_code=404, content={"error": "job not found"})
    return job


# ============================================================
#  文件浏览
# ============================================================

@app.get("/api/scripts", tags=["文件"])
def list_scripts():
    """列出已生成的文案文件。"""
    scripts_dir = Path("outputs/scripts")
    if not scripts_dir.exists():
        return []
    results = []
    for f in scripts_dir.glob("*.*"):
        if f.is_file():
            stat = f.stat()
            results.append({
                "name": f.name,
                "path": str(f),
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })
    results.sort(key=lambda x: x["modified"], reverse=True)
    return results


@app.get("/api/videos", tags=["文件"])
def list_videos():
    """列出已生成的视频任务目录。"""
    videos_dir = Path("outputs/videos")
    if not videos_dir.exists():
        return []
    results = []
    for d in sorted(videos_dir.iterdir(), reverse=True):
        if d.is_dir():
            mp4s = [str(f) for f in d.glob("*.mp4")]
            results.append({"job_id": d.name, "path": str(d), "videos": mp4s})
    return results


@app.get("/api/files/{path:path}", tags=["文件"])
def get_file(path: str):
    """静态文件服务（outputs/ 下的文件）。"""
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = Path(path)
    if not file_path.exists():
        # 也尝试从 outputs/ 下查找
        alt = Path("outputs") / path
        if alt.exists():
            file_path = alt
        else:
            return JSONResponse(status_code=404, content={"error": f"file not found: {path}"})
    if not file_path.is_file():
        return JSONResponse(status_code=400, content={"error": "not a file"})
    return FileResponse(str(file_path))


# ============================================================
#  启动入口
# ============================================================

def start(host: str = "0.0.0.0", port: int = 8000):
    """启动 API 服务。"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)
