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
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout
        logger.info("VisionProvider initialized: base_url=%s model=%s timeout=%ds", base_url, model, timeout)

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
        )

    def review(self, prompt: str, image_paths: list[str | Path]) -> str:
        from openai import OpenAI

        client = OpenAI(base_url=self._base_url, api_key=self._api_key, timeout=self._timeout)
        content = [{"type": "text", "text": prompt}]
        for image_path in image_paths:
            content.append({
                "type": "image_url",
                "image_url": {"url": _data_url(Path(image_path))},
            })

        logger.info("Vision review: model=%s images=%d prompt_len=%d", self._model, len(image_paths), len(prompt))
        response = client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": content}],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        text = response.choices[0].message.content or ""
        logger.info("Vision review response: %d chars", len(text))
        return text


def _data_url(image_path: Path) -> str:
    suffix = image_path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"
