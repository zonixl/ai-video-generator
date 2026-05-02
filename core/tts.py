"""TTS Provider：iFLYTEK API / EdgeTTS。"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import requests

from core.schema import AudioAsset

logger = logging.getLogger(__name__)


class TTSProvider(ABC):
    """配音生成抽象接口。"""

    @abstractmethod
    def synthesize(self, text: str, output_path: str | Path, *, voice: str, rate: float = 1.0) -> AudioAsset:
        ...


class iFLYTEKProvider(TTSProvider):
    """科大讯飞 DTS 大文本合成 Provider。"""

    provider_name = "iflytek"

    def __init__(self, *, host: str, app_id: str, api_key: str, api_secret: str):
        self._host = host
        self._app_id = app_id
        self._api_key = api_key
        self._api_secret = api_secret
        logger.info("iFLYTEKProvider initialized: host=%s app_id=%s", host, app_id[:8] + "***" if app_id else "")

    def synthesize(self, text: str, output_path: str | Path, *, voice: str, rate: float = 1.0) -> AudioAsset:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        iflytek_speed = max(0, min(100, int(rate * 50)))
        logger.info(
            "iFLYTEK TTS start: chars=%d voice=%s speed=%d output=%s",
            len(text), voice, iflytek_speed, output_path,
        )

        task_id = self._create_task(text, voice, iflytek_speed)
        download_url = self._poll_task(task_id)
        self._download(download_url, output_path)
        duration = _audio_duration(output_path)
        logger.info("iFLYTEK TTS done: duration=%.1fs output=%s", duration, output_path)
        return AudioAsset(
            path=str(output_path),
            duration=duration,
            provider=self.provider_name,
            voice=voice,
        )

    def _create_task(self, text: str, voice: str, speed: int) -> str:
        path = "/v1/private/dts_create"
        auth_url = self._assemble_auth_url(path)
        encode_str = base64.encodebytes(text.encode("UTF8")).decode()
        body = {
            "header": {"app_id": self._app_id},
            "parameter": {
                "dts": {
                    "vcn": voice,
                    "language": "zh",
                    "speed": speed,
                    "volume": 50,
                    "pitch": 50,
                    "rhy": 1,
                    "bgs": 0,
                    "reg": 0,
                    "rdn": 0,
                    "scn": 0,
                    "audio": {
                        "encoding": "lame",
                        "sample_rate": 16000,
                        "channels": 1,
                        "bit_depth": 16,
                        "frame_size": 0,
                    },
                    "pybuf": {
                        "encoding": "utf8",
                        "compress": "raw",
                        "format": "plain",
                    },
                }
            },
            "payload": {
                "text": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "plain",
                    "text": encode_str,
                }
            },
        }
        resp = requests.post(auth_url, headers={"Content-Type": "application/json"}, data=json.dumps(body), timeout=30)
        data = resp.json()
        code = data.get("header", {}).get("code")
        if code != 0:
            raise RuntimeError(f"iFLYTEK create task failed: code={code} message={data.get('header', {}).get('message', '')}")
        task_id = data["header"]["task_id"]
        logger.info("iFLYTEK task created: task_id=%s", task_id)
        return task_id

    def _poll_task(self, task_id: str, max_retries: int = 30, interval: float = 2.0) -> str:
        path = "/v1/private/dts_query"
        auth_url = self._assemble_auth_url(path)
        body = {"header": {"app_id": self._app_id, "task_id": task_id}}
        for attempt in range(1, max_retries + 1):
            time.sleep(interval)
            resp = requests.post(auth_url, headers={"Content-Type": "application/json"}, data=json.dumps(body), timeout=30)
            data = resp.json()
            code = data.get("header", {}).get("code")
            if code != 0:
                raise RuntimeError(f"iFLYTEK query task failed: task_id={task_id} code={code}")
            task_status = str(data.get("header", {}).get("task_status", ""))
            if task_status == "5":
                audio_b64 = data.get("payload", {}).get("audio", {}).get("audio", "")
                if not audio_b64:
                    raise RuntimeError(f"iFLYTEK task completed but no audio: task_id={task_id}")
                download_url = base64.b64decode(audio_b64).decode()
                logger.info("iFLYTEK task done: task_id=%s attempt=%d", task_id, attempt)
                return download_url
            logger.debug("iFLYTEK task polling: task_id=%s attempt=%d status=%s", task_id, attempt, task_status)
        raise TimeoutError(f"iFLYTEK task timed out after {max_retries} attempts: task_id={task_id}")

    def _download(self, url: str, output_path: Path) -> None:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        output_path.write_bytes(resp.content)
        logger.debug("iFLYTEK audio downloaded: %d bytes -> %s", len(resp.content), output_path)

    # ---- auth ----
    def _assemble_auth_url(self, path: str) -> str:
        params = self._assemble_auth_params(path)
        return "http://" + self._host + path + "?" + urlencode(params)

    def _assemble_auth_params(self, path: str) -> dict:
        format_date = format_date_time(mktime(datetime.now().timetuple()))
        signature_origin = "host: " + self._host + "\n"
        signature_origin += "date: " + format_date + "\n"
        signature_origin += "POST " + path + " HTTP/1.1"
        signature_sha = hmac.new(
            self._api_secret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature_sha = base64.b64encode(signature_sha).decode("utf-8")
        authorization_origin = 'api_key="%s", algorithm="%s", headers="%s", signature="%s"' % (
            self._api_key, "hmac-sha256", "host date request-line", signature_sha,
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")
        return {
            "host": self._host,
            "date": format_date,
            "authorization": authorization,
        }


class EdgeTTSProvider(TTSProvider):
    """基于 edge-tts 的低成本配音实现（暂时保留）。"""

    provider_name = "edge-tts"

    def synthesize(self, text: str, output_path: str | Path, *, voice: str, rate: float = 1.0) -> AudioAsset:
        try:
            import edge_tts
        except ImportError as exc:
            raise RuntimeError("EdgeTTSProvider 需要安装 edge-tts") from exc

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rate_percent = int((rate - 1.0) * 100)
        rate_text = f"{rate_percent:+d}%"
        logger.info(
            "EdgeTTS start: chars=%d voice=%s rate=%s output=%s",
            len(text), voice, rate_text, output_path,
        )

        async def _run() -> None:
            communicate = edge_tts.Communicate(text, voice=voice, rate=rate_text)
            await communicate.save(str(output_path))

        asyncio.run(_run())
        duration = _audio_duration(output_path)
        logger.info("EdgeTTS done: duration=%.1fs output=%s", duration, output_path)
        return AudioAsset(
            path=str(output_path),
            duration=duration,
            provider=self.provider_name,
            voice=voice,
        )


def _audio_duration(path: str | Path) -> float:
    try:
        from moviepy import AudioFileClip
    except ImportError:
        try:
            from moviepy.editor import AudioFileClip
        except ImportError:
            return 0.0

    clip = AudioFileClip(str(path))
    try:
        return float(clip.duration or 0.0)
    finally:
        clip.close()
