"""TTS Provider：iFLYTEK API / EdgeTTS。"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import re
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
                    "volume": 45,
                    "pitch": 47,
                    "rhy": 0,
                    "bgs": 0,
                    "reg": 0,
                    "rdn": 0,
                    "scn": 0,
                    "audio": {
                        "encoding": "lame",
                        "sample_rate": 24000,
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


class MiMoProvider(TTSProvider):
    """小米 MiMo 语音合成 Provider — 自然语言控制 + 标签控制。"""

    provider_name = "mimo"

    # 硬性约束：附加在 user 指令末尾
    _HARD_RULES = (
        "严格朗读给定文本，一个字都不能多、不能少、不能改。"
        "不要添加任何语气词，不要添加额外声音，不要即兴发挥。"
    )

    MIMO_PRESET_VOICES = {
        "mimo_default", "冰糖", "茉莉", "苏打", "白桦",
        "Mia", "Chloe", "Milo", "Dean",
    }

    def __init__(self, *, base_url: str, api_key: str, model: str):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        logger.info("MiMoProvider initialized: base_url=%s model=%s", self._base_url, model)

    def synthesize(
        self,
        text: str,
        output_path: str | Path,
        *,
        voice: str,
        rate: float = 1.0,
        emotion: str = "",
        use_audio_tag: bool = False,
        audio_format: str = "mp3",
    ) -> AudioAsset:
        from openai import OpenAI

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 音色兜底
        if voice not in self.MIMO_PRESET_VOICES and not voice.startswith("data:"):
            logger.warning("Unknown MiMo voice=%s, fallback to 苏打", voice)
            voice = "苏打"

        # 文本规范化
        clean_text = self.normalize_tts_text(text)

        style_instruction, assistant_text = self.build_voice_prompt(
            clean_text,
            emotion or "娓娓道来",
            intensity="low",
            use_audio_tag=use_audio_tag,
        )

        logger.info(
            "MiMo TTS start: clean_chars=%d voice=%s emotion=%s intensity=low "
            "use_audio_tag=%s format=%s rate_ignored=%s",
            len(clean_text), voice, emotion or "娓娓道来",
            use_audio_tag, audio_format, rate != 1.0,
        )

        if rate != 1.0:
            logger.warning("MiMoProvider: rate parameter is currently ignored for naturalness. rate=%.2f", rate)

        audio_params: dict = {"voice": voice, "format": audio_format}

        client = OpenAI(base_url=self._base_url, api_key=self._api_key, timeout=60)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "user", "content": style_instruction},
                {"role": "assistant", "content": assistant_text},
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

    @staticmethod
    def normalize_tts_text(text: str) -> str:
        """把阅读文案处理成更适合 TTS 朗读的口播文本。"""
        replacements = {
            "AI": "A I",
            "API": "A P I",
            "TTS": "T T S",
            "RAG": "R A G",
            "ComfyUI": "Comfy U I",
            "Claude": "Claude",
            "GPT": "G P T",
            "OpenAI": "Open A I",
            "n8n": "n eight n",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

        text = re.sub(r"[ \t]+", " ", text)

        split_patterns = [
            ("，但是", "。但是"),
            ("，所以", "。所以"),
            ("，因为", "。因为"),
            ("，如果", "。如果"),
            ("，其实", "。其实"),
            ("，然后", "。然后"),
            ("，结果", "。结果"),
            ("，后来", "。后来"),
            ("，而是", "。而是"),
            ("，不是", "。不是"),
            ("，只要", "。只要"),
            ("，问题是", "。问题是"),
        ]
        for old, new in split_patterns:
            text = text.replace(old, new)

        text = re.sub(r"。{2,}", "。", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def build_voice_prompt(
        self,
        text: str,
        emotion: str = "叙事平缓",
        intensity: str = "low",
        use_audio_tag: bool = False,
    ) -> tuple[str, str]:
        BASE_SPEECH_STYLE = (
            "请用自然口语化的中文表达，像一个真实的人在认真发语音或录口播。"
            "整体语气克制、松弛、真实，不要像主播，不要像新闻播报，不要像朗诵，不要像广告配音。"
            "语速中等偏慢，句子之间有自然停顿。"
            "情绪只保留轻微表达，不要夸张表演，不要突然拔高音量，不要故意拖长尾音。"
            "重点词可以轻微强调，但整体听起来要像普通人自然讲话。"
        )

        style_map = {
            "自信坚定": (
                "语气可以稍微更笃定一点，像在分享自己验证过的方法。"
                "有把握，但不要强势，不要喊口号，不要鸡血。"
            ),
            "温柔亲切": (
                "语气稍微温和一点，耐心解释，听起来舒服。"
                "不要撒娇，不要夹子音，不要刻意软。"
            ),
            "娓娓道来": (
                "像日常聊天中讲一件事，有轻微起伏。"
                "不要讲故事腔，不要刻意制造悬念，不要戏剧化。"
            ),
            "严肃沉稳": (
                "语气稍微更认真、更稳一点。"
                "不要新闻腔，不要压低嗓音表演，不要过度沉重。"
            ),
            "兴奋激动": (
                "语气比平时稍微更有精神一点。"
                "像发现一个有用东西分享给朋友，但不要亢奋，不要带货，不要大喊。"
            ),
            "急促紧张": (
                "节奏可以稍微紧一点，像在提醒一个重要问题。"
                "不要慌张，不要喘，不要像警报。"
            ),
            "低沉神秘": (
                "语气可以稍微低一点，有一点悬念感。"
                "不要耳语，不要气泡音，不要恐怖片感觉，不要故意拖尾。"
            ),
            "叙事平缓": (
                "保持自然、平稳、松弛的口播状态。"
                "像在认真讲一件自己的经历，不刻意煽情，不刻意制造起伏。"
            ),
        }

        intensity_map = {
            "low": "情绪强度控制在两分以内，尽量自然克制。",
            "medium": "情绪强度控制在三到四分，有轻微表达起伏。",
            "high": "情绪可以更明显，但仍然不要夸张表演。",
        }

        negative_style = (
            "不要使用播音腔、朗诵腔、广告腔、带货腔、短视频鸡血感。"
            "不要过度抑扬顿挫，不要夸张停顿，不要故意拖长尾音。"
            "不要突然提高音量，不要像在演戏，不要像在配小说。"
        )

        tag_map = {
            "自信坚定": "平静",
            "温柔亲切": "温柔",
            "娓娓道来": "平静",
            "严肃沉稳": "严肃",
            "兴奋激动": "开心",
            "急促紧张": "紧张",
            "低沉神秘": "深沉",
            "叙事平缓": "平静",
        }

        style = style_map.get(emotion, style_map["叙事平缓"])
        intensity_text = intensity_map.get(intensity, intensity_map["low"])

        voice_prompt = (
            BASE_SPEECH_STYLE
            + style
            + intensity_text
            + negative_style
            + self._HARD_RULES
            + "请优先保证自然度，而不是情绪表现力。"
        )

        if use_audio_tag:
            tags = tag_map.get(emotion, "平静")
            assistant_text = f"({tags}){text}"
        else:
            assistant_text = text

        return voice_prompt, assistant_text


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
