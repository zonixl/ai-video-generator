"""字幕文件生成工具。"""

from __future__ import annotations

from pathlib import Path
import textwrap

from core.schema import VideoPlan


def format_srt_timestamp(seconds: float) -> str:
    """把秒数格式化为 SRT 时间戳。"""
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def split_subtitle_lines(text: str, max_chars: int = 20) -> str:
    """按中文短视频字幕习惯切成多行。"""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return "\n".join(textwrap.wrap(text, width=max_chars, break_long_words=True))


def build_srt(plan: VideoPlan, max_chars: int = 20) -> str:
    """根据分镜时间轴生成 SRT 内容。"""
    blocks = []
    start = 0.0
    for subtitle_index, scene in enumerate(plan.scenes, start=1):
        end = start + scene.duration
        blocks.append(
            "\n".join(
                [
                    str(subtitle_index),
                    f"{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}",
                    split_subtitle_lines(scene.subtitle, max_chars=max_chars),
                ]
            )
        )
        start = end
    return "\n\n".join(blocks) + "\n"


def write_srt(plan: VideoPlan, output_path: str | Path, max_chars: int = 20) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_srt(plan, max_chars=max_chars), encoding="utf-8")
    return output_path

