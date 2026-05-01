"""多模型统一管理：Provider（连接）+ Instance（任务）→ ModelManager。"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Provider 接口 + 实现
# ═══════════════════════════════════════════════════════════════

class BaseProvider(ABC):
    """LLM Provider 抽象基类。"""

    @abstractmethod
    def generate(self, model: str, prompt: str,
                 system_prompt: str | None,
                 temperature: float, max_tokens: int) -> str:
        ...

    @abstractmethod
    def generate_stream(self, model: str, prompt: str,
                        system_prompt: str | None,
                        temperature: float, max_tokens: int) -> Iterator[str]:
        ...


class OllamaProvider(BaseProvider):
    """Ollama 本地/远程 Provider。"""

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 300):
        self._base_url = base_url
        self._timeout = timeout
        logger.info("OllamaProvider initialized: base_url=%s timeout=%ds", base_url, timeout)

    def generate(self, model: str, prompt: str,
                 system_prompt: str | None,
                 temperature: float, max_tokens: int) -> str:
        import ollama

        logger.info("Ollama generate: model=%s prompt_len=%d temp=%.2f max_tokens=%d",
                    model, len(prompt), temperature, max_tokens)
        logger.debug("Prompt preview: %s...", prompt[:200].replace("\n", "\\n"))

        messages = self._build_messages(prompt, system_prompt)
        response = ollama.chat(
            model=model,
            messages=messages,
            options={"temperature": temperature, "num_predict": max_tokens},
        )
        content = response["message"]["content"]
        logger.info("Ollama response: %d chars", len(content))
        return content

    def generate_stream(self, model: str, prompt: str,
                        system_prompt: str | None,
                        temperature: float, max_tokens: int) -> Iterator[str]:
        import ollama

        messages = self._build_messages(prompt, system_prompt)
        stream = ollama.chat(
            model=model,
            messages=messages,
            stream=True,
            options={"temperature": temperature, "num_predict": max_tokens},
        )
        for chunk in stream:
            if "message" in chunk and "content" in chunk["message"]:
                yield chunk["message"]["content"]

    def _build_messages(self, prompt: str, system_prompt: str | None) -> list[dict]:
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": prompt})
        return msgs


class OpenAICompatibleProvider(BaseProvider):
    """OpenAI 兼容 API Provider（OpenAI / DeepSeek / vLLM / 等）。"""

    def __init__(self, base_url: str, api_key: str, timeout: int = 120):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        logger.info("OpenAICompatibleProvider initialized: base_url=%s timeout=%ds", base_url, timeout)

    def _get_client(self):
        from openai import OpenAI
        return OpenAI(base_url=self._base_url, api_key=self._api_key,
                      timeout=self._timeout)

    def generate(self, model: str, prompt: str,
                 system_prompt: str | None,
                 temperature: float, max_tokens: int) -> str:
        logger.info("OpenAI generate: model=%s prompt_len=%d temp=%.2f max_tokens=%d",
                    model, len(prompt), temperature, max_tokens)
        logger.debug("Prompt preview: %s...", prompt[:200].replace("\n", "\\n"))

        client = self._get_client()
        messages = self._build_messages(prompt, system_prompt)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        logger.info("OpenAI response: %d chars", len(content))
        return content

    def generate_stream(self, model: str, prompt: str,
                        system_prompt: str | None,
                        temperature: float, max_tokens: int) -> Iterator[str]:
        client = self._get_client()
        messages = self._build_messages(prompt, system_prompt)
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _build_messages(self, prompt: str, system_prompt: str | None) -> list[dict]:
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": prompt})
        return msgs


# ═══════════════════════════════════════════════════════════════
# Provider 工厂
# ═══════════════════════════════════════════════════════════════

def _create_provider(name: str, cfg: dict) -> BaseProvider:
    """根据配置字典创建 Provider 实例。"""
    ptype = cfg.get("type", "ollama")
    logger.debug("Creating provider '%s': type=%s", name, ptype)
    if ptype == "ollama":
        return OllamaProvider(
            base_url=cfg.get("base_url", "http://localhost:11434"),
            timeout=cfg.get("timeout", 300),
        )
    elif ptype == "openai_compatible":
        return OpenAICompatibleProvider(
            base_url=cfg["base_url"],
            api_key=cfg.get("api_key", ""),
            timeout=cfg.get("timeout", 120),
        )
    else:
        raise ValueError(f"Unknown provider type: {ptype}")


# ═══════════════════════════════════════════════════════════════
# ModelManager
# ═══════════════════════════════════════════════════════════════

class ModelManager:
    """统一模型管理器。"""

    def __init__(self, providers_cfg: dict, instances_cfg: dict):
        self._provider_cfgs = providers_cfg
        self._instances = instances_cfg
        self._providers: dict[str, BaseProvider] = {}
        logger.info("ModelManager initialized: %d providers, %d instances",
                    len(providers_cfg), len(instances_cfg))
        logger.debug("Available instances: %s", list(instances_cfg.keys()))

    def generate(self, instance_name: str, prompt: str,
                 system_prompt: str | None = None) -> str:
        """使用指定 instance 生成响应。"""
        inst = self._get_instance(instance_name)
        provider = self._get_provider(inst["provider"])
        logger.info("ModelManager.generate: instance=%s provider=%s model=%s",
                    instance_name, inst["provider"], inst["model"])
        return provider.generate(
            model=inst["model"],
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=inst.get("temperature", 0.7),
            max_tokens=inst.get("max_tokens", 2048),
        )

    def generate_stream(self, instance_name: str, prompt: str,
                        system_prompt: str | None = None) -> Iterator[str]:
        """使用指定 instance 流式生成。"""
        inst = self._get_instance(instance_name)
        provider = self._get_provider(inst["provider"])
        yield from provider.generate_stream(
            model=inst["model"],
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=inst.get("temperature", 0.7),
            max_tokens=inst.get("max_tokens", 2048),
        )

    def list_instances(self) -> list[str]:
        return list(self._instances.keys())

    def _get_instance(self, name: str) -> dict:
        if name not in self._instances:
            raise KeyError(f"Unknown model instance: {name}. "
                           f"Available: {list(self._instances.keys())}")
        return self._instances[name]

    def _get_provider(self, name: str) -> BaseProvider:
        if name not in self._providers:
            if name not in self._provider_cfgs:
                raise KeyError(f"Unknown provider: {name}. "
                               f"Available: {list(self._provider_cfgs.keys())}")
            self._providers[name] = _create_provider(name, self._provider_cfgs[name])
        return self._providers[name]
