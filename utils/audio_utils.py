"""音频工具：格式转换、静音检测、分片。"""

from pathlib import Path
import subprocess
import tempfile


def convert_to_wav(input_path: str | Path, output_path: str | Path | None = None,
                   sample_rate: int = 16000) -> Path:
    """使用 ffmpeg 将任意音频转为 16kHz 单声道 WAV。"""
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.with_suffix(".wav")
    else:
        output_path = Path(output_path)

    subprocess.run([
        "ffmpeg", "-y", "-i", str(input_path),
        "-ac", "1", "-ar", str(sample_rate),
        "-sample_fmt", "s16", str(output_path)
    ], capture_output=True, check=True)
    return output_path


def split_by_silence(
    audio_path: str | Path,
    silence_threshold: int = -40,
    min_silence_duration: float = 1.0,
    output_dir: str | Path | None = None
) -> list[Path]:
    """使用 pydub 按静音切分音频。返回分片路径列表。

    如果音频本身就很短（< silence_duration × 3），跳过切分直接返回原文件。
    """
    from pydub import AudioSegment
    from pydub.silence import split_on_silence

    audio_path = Path(audio_path)
    audio = AudioSegment.from_file(audio_path)

    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="audio_chunks_"))
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    min_silence_ms = int(min_silence_duration * 1000)
    chunks = split_on_silence(
        audio,
        min_silence_len=min_silence_ms,
        silence_thresh=silence_threshold,
        keep_silence=300  # 保留300ms边距
    )

    if not chunks:
        # 没有检测到静音 → 整段作为一个chunk
        chunks = [audio]

    result_paths = []
    for i, chunk in enumerate(chunks):
        chunk_path = output_dir / f"chunk_{i:04d}.wav"
        chunk.export(chunk_path, format="wav")
        result_paths.append(chunk_path)

    return result_paths


def get_audio_duration(audio_path: str | Path) -> float:
    """获取音频时长（秒）。"""
    from pydub import AudioSegment
    audio = AudioSegment.from_file(audio_path)
    return len(audio) / 1000.0
