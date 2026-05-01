"""媒体产物路径和通用工具。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def make_job_id(prefix: str = "video") -> str:
    """生成一次视频生产任务的 ID。"""
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def safe_stem(text: str, fallback: str = "video", limit: int = 40) -> str:
    """把标题转换成安全文件名片段。"""
    stem = "".join(char for char in text if char.isalnum() or char in "._- ").strip()
    return (stem[:limit] or fallback).strip()


def scene_filename(scene_index: int, suffix: str) -> str:
    return f"scene_{scene_index:03d}{suffix}"

