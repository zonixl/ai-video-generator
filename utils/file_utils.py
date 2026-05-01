"""文件工具：读写、hash、格式校验。"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
import hashlib
import json


def read_text(file_path: str | Path) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(file_path: str | Path, content: str):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def write_json(file_path: str | Path, data: dict | list):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_json(file_path: str | Path) -> dict | list:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_transcript(text: str, source_file: str | Path, output_dir: str | Path) -> Path:
    """保存转写文本，自动加时间戳防止覆盖。"""
    source_name = Path(source_file).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{source_name}_{timestamp}.txt"
    output_path = Path(output_dir) / filename
    write_text(output_path, text)
    return output_path


def save_script(text: str, topic: str, output_dir: str | Path) -> Path:
    """保存生成的文案。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # topic 作为文件名的一部分（只保留中文、字母、数字）
    safe_topic = "".join(c for c in topic if c.isalnum() or c in "._- ")[:30].strip()
    filename = f"{safe_topic}_{timestamp}.md"
    output_path = output_dir / filename
    write_text(output_path, text)
    return output_path


def file_hash(file_path: str | Path) -> str:
    """文件的MD5哈希（用于去重检测）。"""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def is_audio_file(file_path: str | Path) -> bool:
    """检查是否为支持的音频格式。"""
    suffix = Path(file_path).suffix.lower()
    return suffix in {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".opus"}
