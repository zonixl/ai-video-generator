"""视频生成 Provider（Seedance API）。"""

from __future__ import annotations

import base64
import logging
import time
from pathlib import Path
from urllib.request import urlopen

import requests

logger = logging.getLogger(__name__)


class SeedanceVideoProvider:
    """火山 Ark Seedance 视频生成 Provider — 图生视频-首帧模式。"""

    provider_name = "seedance"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        resolution: str = "720p",
        ratio: str = "9:16",
        duration: int = 5,
        generate_audio: bool = False,
        watermark: bool = False,
        timeout: int = 300,
        poll_interval: float = 5.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._resolution = resolution
        self._ratio = ratio
        self._duration = duration
        self._generate_audio = generate_audio
        self._watermark = watermark
        self._timeout = timeout
        self._poll_interval = poll_interval
        logger.info(
            "SeedanceVideoProvider initialized: model=%s resolution=%s ratio=%s duration=%ds audio=%s",
            model, resolution, ratio, duration, generate_audio,
        )

    def generate(
        self,
        first_frame_path: str | Path,
        prompt: str,
        output_path: str | Path,
        *,
        duration: int | None = None,
    ) -> str:
        """图生视频-首帧：首帧图片 + 文本提示词 → 视频文件。"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 编码首帧图片
        image_b64 = self._encode_image(first_frame_path)
        duration = duration or self._duration

        logger.info(
            "Seedance generate start: model=%s first_frame=%s duration=%ds prompt_len=%d",
            self._model, Path(first_frame_path).name, duration, len(prompt),
        )

        task_id = self._create_task(image_b64, prompt, duration)
        video_url = self._poll_task(task_id)
        self._download(video_url, output_path)
        logger.info("Seedance generate done: %s", output_path)
        return str(output_path)

    def _create_task(self, image_b64: str, prompt: str, duration: int) -> str:
        url = f"{self._base_url}/contents/generations/tasks"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model,
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": image_b64},
                    "role": "first_frame",
                },
                {"type": "text", "text": prompt},
            ],
            "resolution": self._resolution,
            "ratio": self._ratio,
            "duration": duration,
            "generate_audio": self._generate_audio,
            "watermark": self._watermark,
        }
        resp = requests.post(url, json=body, headers=headers, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Seedance create task failed: HTTP {resp.status_code} {resp.text[:500]}"
            )
        data = resp.json()
        task_id = data.get("id")
        if not task_id:
            raise RuntimeError(f"Seedance create task: no id in response: {data}")
        logger.info("Seedance task created: %s", task_id)
        return task_id

    def _poll_task(self, task_id: str) -> str:
        url = f"{self._base_url}/contents/generations/tasks/{task_id}"
        headers = {"Authorization": f"Bearer {self._api_key}"}
        deadline = time.time() + self._timeout
        last_status = ""

        while time.time() < deadline:
            time.sleep(self._poll_interval)
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code != 200:
                logger.warning("Seedance poll failed: HTTP %d %s", resp.status_code, resp.text[:200])
                continue
            data = resp.json()
            status = data.get("status", "")

            if status != last_status:
                logger.info("Seedance task %s: status=%s", task_id, status)
                last_status = status

            if status == "succeeded":
                video_url = (
                    data.get("content", {}).get("video", {}).get("url", "")
                )
                if not video_url:
                    raise RuntimeError(f"Seedance succeeded but no video URL: {data}")
                return video_url

            if status == "failed":
                error = data.get("error", {})
                raise RuntimeError(f"Seedance task failed: {error}")

        raise TimeoutError(f"Seedance task timed out after {self._timeout}s: {task_id}")

    def _download(self, url: str, output_path: Path) -> None:
        with urlopen(url, timeout=self._timeout) as resp:
            output_path.write_bytes(resp.read())
        logger.debug("Seedance video downloaded: %d bytes -> %s", output_path.stat().st_size, output_path)

    def _encode_image(self, image_path: str | Path) -> str:
        """将本地图片编码为 base64 data URI。"""
        image_path = Path(image_path)
        suffix = image_path.suffix.lower()
        mime = {
            ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp", ".bmp": "image/bmp",
        }.get(suffix, "image/png")
        b64 = base64.b64encode(image_path.read_bytes()).decode()
        return f"data:{mime};base64,{b64}"
