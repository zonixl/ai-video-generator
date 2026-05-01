"""统一配置入口：读取 config.yaml，支持环境变量覆盖（前缀 AI_）。

用法：
    from config import Settings
    cfg = Settings()
    print(cfg.stt_model_size)
"""

import os
import re
from pathlib import Path

import yaml


def _resolve_env_vars(value: str) -> str:
    """解析字符串中的 ${VAR_NAME} 环境变量引用。"""
    if not isinstance(value, str):
        return value
    pattern = re.compile(r"\$\{(\w+)\}")
    def _replacer(m):
        return os.environ.get(m.group(1), "")
    return pattern.sub(_replacer, value)


class Settings:
    """从 YAML 文件加载配置，扁平化为一级属性。环境变量 AI_<KEY> 可覆盖。"""

    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        self._config_path = Path(config_path)
        self._flat: dict = {}
        self._load()

    def _load(self):
        with open(self._config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        for section, values in data.items():
            if not isinstance(values, dict):
                self._flat[section] = values
                continue
            for key, val in values.items():
                env_key = f"AI_{section.upper()}_{key.upper()}"
                env_val = os.environ.get(env_key)

                if env_val is not None:
                    if isinstance(val, bool):
                        final_val = env_val.lower() in ("1", "true", "yes")
                    elif isinstance(val, int):
                        final_val = int(env_val)
                    elif isinstance(val, float):
                        final_val = float(env_val)
                    else:
                        final_val = _resolve_env_vars(env_val)
                else:
                    final_val = _resolve_env_vars(val)
                self._flat[f"{section}_{key}"] = final_val

    def _get(self, key: str, default=None):
        return self._flat.get(key, default)

    def _resolve_path(self, key: str) -> Path:
        p = Path(self._get(key, "."))
        if p.is_absolute():
            return p
        root = self._config_path.parent.parent
        return (root / p).resolve()

    # ---- 便捷属性 ----
    @property
    def stt_model_size(self) -> str:           return self._get("stt_model_size")
    @property
    def stt_device(self) -> str:                return self._get("stt_device")
    @property
    def stt_compute_type(self) -> str:          return self._get("stt_compute_type")
    @property
    def stt_language(self) -> str | None:       return self._get("stt_language") or None

    @property
    def embedding_model_name(self) -> str:      return self._get("embedding_model_name")
    @property
    def embedding_device(self) -> str:          return self._get("embedding_device")
    @property
    def embedding_normalize(self) -> bool:      return self._get("embedding_normalize")

    @property
    def vectordb_persist_dir(self) -> Path:     return self._resolve_path("vectordb_persist_dir")
    @property
    def vectordb_collection_name(self) -> str:  return self._get("vectordb_collection_name")

    @property
    def retrieval_strategy(self) -> str:        return self._get("retrieval_strategy")
    @property
    def retrieval_top_k(self) -> int:           return self._get("retrieval_top_k")
    @property
    def retrieval_mmr_lambda(self) -> float:    return self._get("retrieval_mmr_lambda")

    @property
    def audio_silence_threshold(self) -> int:   return self._get("audio_silence_threshold")
    @property
    def audio_min_silence_duration(self) -> float: return self._get("audio_min_silence_duration")
    @property
    def audio_chunk_max_duration(self) -> int:  return self._get("audio_chunk_max_duration")

    @property
    def text_chunk_size(self) -> int:           return self._get("text_chunk_size")
    @property
    def text_chunk_overlap(self) -> int:        return self._get("text_chunk_overlap")

    @property
    def output_transcripts_dir(self) -> Path:   return self._resolve_path("output_transcripts_dir")
    @property
    def output_scripts_dir(self) -> Path:       return self._resolve_path("output_scripts_dir")
    @property
    def output_audio_dir(self) -> Path:         return self._resolve_path("output_audio_dir")
    @property
    def output_images_dir(self) -> Path:        return self._resolve_path("output_images_dir")

    # ---- logging 段 ----
    @property
    def logging_level(self) -> str:             return self._get("logging_level", "INFO")
    @property
    def logging_file(self) -> Path:             return self._resolve_path("logging_file")
    @property
    def logging_file_level(self) -> str:        return self._get("logging_file_level", "DEBUG")
    @property
    def logging_format(self) -> str:            return self._get("logging_format", "%(asctime)s [%(levelname)-5s] [%(name)s] %(message)s")
    @property
    def logging_datefmt(self) -> str:           return self._get("logging_datefmt", "%Y-%m-%d %H:%M:%S")

    # ---- models 段（结构化返回） ----
    @property
    def models_providers(self) -> dict:
        """返回 providers 字典，已解析环境变量。"""
        return self._get("models_providers", {})

    @property
    def models_instances(self) -> dict:
        """返回 instances 字典，已解析环境变量。"""
        return self._get("models_instances", {})

    @property
    def models_default_instance(self) -> str:
        return self._get("models_default_instance", "")
