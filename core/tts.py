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
    def synthesize(self, text: str, output_path: str | Path, *, voice: str, rate: float = 1.0, emotion: str = "") -> AudioAsset:
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

    def synthesize(self, text: str, output_path: str | Path, *, voice: str, rate: float = 1.0, emotion: str = "") -> AudioAsset:
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
        logger.debug("iFLYTEK create: http=%d body_preview=%s", resp.status_code, resp.text[:500])
        if resp.status_code != 200:
            raise RuntimeError(f"iFLYTEK create task http error: status={resp.status_code} body={resp.text[:500]}")
        try:
            data = resp.json()
        except Exception:
            raise RuntimeError(f"iFLYTEK create task returned non-JSON (http={resp.status_code}): {resp.text[:500]}")
        # 先检查顶层错误码（auth失败等）
        top_code = data.get("code")
        if top_code is not None and top_code != 0:
            raise RuntimeError(f"iFLYTEK create task error: code={top_code} message={data.get('message', '')}")
        # 正常响应的 code 在 header 中
        header = data.get("header", {})
        code = header.get("code")
        if code != 0:
            raise RuntimeError(f"iFLYTEK create task failed: code={code} message={header.get('message', '')} full_header={header}")
        task_id = header.get("task_id")
        if not task_id:
            raise RuntimeError(f"iFLYTEK create task: no task_id in response, keys={list(data.keys())}")
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
            top_code = data.get("code")
            if top_code is not None and top_code != 0:
                raise RuntimeError(f"iFLYTEK query task error: code={top_code} message={data.get('message', '')}")
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


# ---- MiMo 风格预设 — 自然语言控制（user）+ 标签控制（assistant）----
# user 内容：一句自然语言描述风格
# assistant 内容：(标签)待合成文本
MIMO_STYLES: dict[str, str] = {}
MIMO_STYLES["自信坚定"] = (
    "用沉稳自信的语调分享一个确信有用的方法论，语气松弛有亲和力，像过来人在跟好朋友说掏心窝子的话，"
    "遇到关键词时微微加重强调。"
)
MIMO_STYLES["温柔亲切"] = (
    "用温柔轻声的语调分享心得，音色偏暖偏轻，不赶时间不刻意，像在安慰人，句尾轻轻软下来，让人觉得舒服放松。"
)
MIMO_STYLES["娓娓道来"] = (
    "像在饭桌上跟朋友讲一件有意思的事，语调有明显的起伏，像波浪一样有高有低，生动自然地聊天。"
)
MIMO_STYLES["严肃沉稳"] = (
    "用深沉郑重的语调说一个被忽视的事实，音色偏低沉，每个字都咬得很稳，句间留稍长停顿让人消化。"
)
MIMO_STYLES["兴奋激动"] = (
    "像刚查到惊喜结果忍不住告诉同事，声音明亮有穿透力，句尾微微上扬带着压不住的兴奋，真实的开心。"
)
MIMO_STYLES["急促紧张"] = (
    "用紧凑有力的语调传递信息，制造连贯的紧迫感，在最重要的词上加重语气形成反差，像在紧急提醒。"
)
MIMO_STYLES["低沉神秘"] = (
    "像在黑暗房间里对一小群人讲秘密，声音不大但每个字都让人想听下去，气声比例高，尾音微微拖一点，深夜电台的低语感。"
)
MIMO_STYLES["叙事平缓"] = (
    "用最自然松弛的语气分享观点，像跟朋友发语音消息一样，不端不播音腔，开头稍微提气吸引注意，中间平缓展开，结尾微微加重收束。"
)

MIMO_DEFAULT_STYLE = MIMO_STYLES["叙事平缓"]

class MiMoProvider(TTSProvider):
    """小米 MiMo 语音合成 Provider — 自然语言控制 + 标签控制。"""

    provider_name = "mimo"

    # 硬性约束：附加在 user 指令末尾
    _HARD_RULES = (
        "严格朗读给定文本，一个字都不能多、不能少、不能改。"
        "不要添加任何语气词，不要添加额外声音，不要即兴发挥。"
    )

    def __init__(self, *, base_url: str, api_key: str, model: str):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        logger.info("MiMoProvider initialized: base_url=%s model=%s", self._base_url, model)

    def synthesize(self, text: str, output_path: str | Path, *, voice: str, rate: float = 1.0, emotion: str = "") -> AudioAsset:
        from openai import OpenAI

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # user: 自然语言风格指令 + 硬性约束
        style_instruction = MIMO_STYLES.get(emotion, MIMO_DEFAULT_STYLE) + self._HARD_RULES

        # assistant: 标签控制 — 在文本前加风格标签
        tag_map = {
            "自信坚定": "自信 从容",
            "温柔亲切": "温柔 轻声",
            "娓娓道来": "从容 自然",
            "严肃沉稳": "沉稳 郑重",
            "兴奋激动": "兴奋 明亮",
            "急促紧张": "急促 紧凑",
            "低沉神秘": "低沉 神秘",
            "叙事平缓": "自然 松弛",
        }
        tags = tag_map.get(emotion, "自然")
        tagged_text = f"({tags}){text}"

        logger.info(
            "MiMo TTS start: chars=%d voice=%s emotion=%s rate=%.2f",
            len(text), voice, emotion or "default", rate,
        )

        # 构建 audio 参数，统一语速
        audio_params: dict = {"voice": voice, "format": "mp3"}
        if rate != 1.0:
            speed = int(rate * 100)
            audio_params["speed"] = max(50, min(200, speed))

        client = OpenAI(base_url=self._base_url, api_key=self._api_key, timeout=60)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "user", "content": style_instruction},
                {"role": "assistant", "content": tagged_text},
            ],
            extra_body={"audio": audio_params},
        )

        # 提取 base64 音频
        audio_b64 = self._extract_audio(response)
        if not audio_b64:
            raise RuntimeError("MiMo API returned no audio data")

        output_path.write_bytes(base64.b64decode(audio_b64))
        duration = _audio_duration(output_path)
        logger.info("MiMo TTS done: duration=%.1fs output=%s", duration, output_path)
        return AudioAsset(
            path=str(output_path),
            duration=duration,
            provider=self.provider_name,
            voice=voice,
        )

    def _extract_audio(self, response) -> str | None:
        """从 OpenAI-compatible 响应中提取 base64 音频数据。"""
        if not response.choices:
            return None
        msg = response.choices[0].message

        # OpenAI audio output format
        audio = getattr(msg, "audio", None)
        if audio and hasattr(audio, "data"):
            logger.debug("MiMo audio extracted from message.audio.data (%d chars)", len(audio.data))
            return audio.data

        # Fallback: check model_extra / dict
        raw = getattr(msg, "model_extra", {}) or {}
        if "audio" in raw:
            data = raw["audio"].get("data") or raw["audio"].get("audio")
            if data:
                return data

        # Fallback: check content for audio
        content = getattr(msg, "content", "")
        if isinstance(content, str) and len(content) > 100:
            logger.warning("MiMo: content field has %d chars - not typical audio", len(content))

        logger.error("MiMo: could not extract audio from response. msg keys: %s",
                     list(raw.keys()) if raw else type(msg).__name__)
        return None


class EdgeTTSProvider(TTSProvider):
    """基于 edge-tts 的低成本配音实现（暂时保留）。"""

    provider_name = "edge-tts"

    def synthesize(self, text: str, output_path: str | Path, *, voice: str, rate: float = 1.0, emotion: str = "") -> AudioAsset:
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
