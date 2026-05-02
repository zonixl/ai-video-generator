"""多模态视觉模型 Provider。"""

from __future__ import annotations

import base64
import logging
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class VisionProvider(ABC):
    """视觉模型抽象接口。"""

    @abstractmethod
    def review(self, prompt: str, image_paths: list[str | Path]) -> str:
        ...


class OpenAICompatibleVisionProvider(VisionProvider):
    """OpenAI-compatible vision chat API Provider。"""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        timeout: int = 120,
        image_format: str = "openai",
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._image_format = image_format
        logger.info(
            "VisionProvider initialized: base_url=%s model=%s timeout=%ds image_format=%s",
            base_url, model, timeout, image_format,
        )

    @classmethod
    def from_model_config(cls, providers_cfg: dict, instances_cfg: dict, instance_name: str):
        instance = instances_cfg[instance_name]
        provider = providers_cfg[instance["provider"]]
        return cls(
            base_url=provider["base_url"],
            api_key=provider.get("api_key", ""),
            model=instance["model"],
            temperature=instance.get("temperature", 0.1),
            max_tokens=instance.get("max_tokens", 4096),
            timeout=provider.get("timeout", 120),
            image_format=provider.get("image_format", "openai"),
        )

    def review(self, prompt: str, image_paths: list[str | Path]) -> str:
        from openai import OpenAI

        client = OpenAI(base_url=self._base_url, api_key=self._api_key, timeout=self._timeout)
        content = []
        for image_path in image_paths:
            content.append(_image_content(_data_url(Path(image_path)), self._image_format))
        content.append({"type": "text", "text": prompt})

        logger.info("Vision review: model=%s images=%d prompt_len=%d", self._model, len(image_paths), len(prompt))
        response = client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": content}],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        text = _extract_response_text(response)
        if not text.strip():
            payload = response.model_dump() if hasattr(response, "model_dump") else {}
            logger.error("Vision provider returned empty response: %s", _summarize_response(payload))
            raise RuntimeError("Vision provider returned empty response")
        logger.info("Vision review response: %d chars", len(text))
        return text


def _data_url(image_path: Path) -> str:
    suffix = image_path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _image_content(data_url: str, image_format: str) -> dict:
    if image_format == "image":
        return {"type": "image", "image": data_url}
    if image_format == "image_url_string":
        return {"type": "image_url", "image_url": data_url}
    if image_format == "input_image":
        return {"type": "input_image", "image_url": data_url}
    return {"type": "image_url", "image_url": {"url": data_url}}


def _extract_response_text(response) -> str:
    if not response.choices:
        return ""
    message = response.choices[0].message
    content = getattr(message, "content", "") or ""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = "\n".join(
            str(item.get("text", "")) if isinstance(item, dict) else str(item)
            for item in content
        )
    else:
        text = str(content)
    if text.strip():
        return text

    for attr in ("reasoning_content", "reasoning", "text", "output_text"):
        value = getattr(message, attr, None)
        if isinstance(value, str) and value.strip():
            return value

    if hasattr(message, "model_dump"):
        data = message.model_dump()
        for key in ("reasoning_content", "reasoning", "text", "output_text"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return ""


def _summarize_response(payload: dict) -> dict:
    choices = payload.get("choices", [])
    summary = {
        "id": payload.get("id"),
        "model": payload.get("model"),
        "usage": payload.get("usage"),
        "choices_count": len(choices) if isinstance(choices, list) else 0,
    }
    if choices:
        choice = choices[0]
        summary["finish_reason"] = choice.get("finish_reason")
        message = choice.get("message") or {}
        summary["message_keys"] = sorted(message.keys())
        summary["content_preview"] = str(message.get("content", ""))[:120]
    return summary
