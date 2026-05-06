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


def _resolve_config_value(value):
    if isinstance(value, str):
        return _resolve_env_vars(value)
    if isinstance(value, dict):
        return {key: _resolve_config_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_config_value(item) for item in value]
    return value


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
                        final_val = _resolve_config_value(env_val)
                else:
                    final_val = _resolve_config_value(val)
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
    def ingest_parallel_workers(self) -> int:   return self._get("ingest_parallel_workers", 2)
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
    @property
    def output_videos_dir(self) -> Path:        return self._resolve_path("output_videos_dir")
    @property
    def output_clips_dir(self) -> Path:         return self._resolve_path("output_clips_dir")
    @property
    def output_subtitles_dir(self) -> Path:     return self._resolve_path("output_subtitles_dir")
    @property
    def output_plans_dir(self) -> Path:         return self._resolve_path("output_plans_dir")
    @property
    def output_remotion_dir(self) -> Path:      return self._resolve_path("output_remotion_dir")
    @property
    def output_video_reviews_dir(self) -> Path: return self._resolve_path("output_video_reviews_dir")
    @property
    def output_tweets_dir(self) -> Path:       return self._resolve_path("output_tweets_dir")

    # ---- tts 段 ----
    @property
    def tts_engine(self) -> str:                return self._get("tts_engine", "mimo")
    @property
    def tts_voice(self) -> str:                 return self._get("tts_voice", "冰糖")
    @property
    def tts_speed(self) -> float:               return self._get("tts_speed", 1.0)
    # iflytek — 嵌套在 tts.iflytek 下，需从字典中提取
    @property
    def tts_iflytek_host(self) -> str:          return self._get_nested("tts_iflytek", "host", "api-dx.xf-yun.com")
    @property
    def tts_iflytek_app_id(self) -> str:        return self._get_nested("tts_iflytek", "app_id", "")
    @property
    def tts_iflytek_api_key(self) -> str:       return self._get_nested("tts_iflytek", "api_key", "")
    @property
    def tts_iflytek_api_secret(self) -> str:    return self._get_nested("tts_iflytek", "api_secret", "")

    # mimo — 嵌套在 tts.mimo 下
    @property
    def tts_mimo_base_url(self) -> str:         return self._get_nested("tts_mimo", "base_url", "https://api.xiaomimimo.com/v1")
    @property
    def tts_mimo_api_key(self) -> str:          return self._get_nested("tts_mimo", "api_key", "")
    @property
    def tts_mimo_model(self) -> str:            return self._get_nested("tts_mimo", "model", "mimo-v2.5-tts")
    @property
    def tts_mode(self) -> str:                  return self._get("tts_mode", "per_scene")

    def _get_nested(self, parent_key: str, child_key: str, default: str = "") -> str:
        nested = self._get(parent_key, {})
        if isinstance(nested, dict):
            return nested.get(child_key, default)
        return default

    # ---- image_gen 段 ----
    @property
    def image_gen_engine(self) -> str:          return self._get("image_gen_engine", "placeholder")
    @property
    def image_gen_base_url(self) -> str:        return self._get("image_gen_base_url", "")
    @property
    def image_gen_api_key(self) -> str:         return self._get("image_gen_api_key", "")
    @property
    def image_gen_model(self) -> str:           return self._get("image_gen_model", "")
    @property
    def image_gen_size(self) -> str:            return self._get("image_gen_size", "2K")
    @property
    def image_gen_watermark(self) -> bool:      return self._get("image_gen_watermark", True)
    @property
    def image_gen_quality(self) -> str:         return self._get("image_gen_quality", "auto")
    @property
    def image_gen_width(self) -> int:           return self._get("image_gen_width", 1080)
    @property
    def image_gen_height(self) -> int:          return self._get("image_gen_height", 1920)

    # ---- video_gen 段 ----
    @property
    def video_gen_engine(self) -> str:          return self._get("video_gen_engine", "disabled")
    @property
    def video_gen_base_url(self) -> str:        return self._get("video_gen_base_url", "")
    @property
    def video_gen_api_key(self) -> str:         return self._get("video_gen_api_key", "")
    @property
    def video_gen_model(self) -> str:           return self._get("video_gen_model", "")
    @property
    def video_gen_resolution(self) -> str:      return self._get("video_gen_resolution", "720p")
    @property
    def video_gen_ratio(self) -> str:           return self._get("video_gen_ratio", "9:16")
    @property
    def video_gen_duration(self) -> int:        return self._get("video_gen_duration", 5)
    @property
    def video_gen_generate_audio(self) -> bool: return self._get("video_gen_generate_audio", False)
    @property
    def video_gen_watermark(self) -> bool:      return self._get("video_gen_watermark", False)
    @property
    def video_gen_timeout(self) -> int:         return self._get("video_gen_timeout", 300)
    @property
    def video_gen_poll_interval(self) -> float: return self._get("video_gen_poll_interval", 5.0)

    # ---- video 段 ----
    @property
    def video_scene_splitter(self) -> str:      return self._get("video_scene_splitter", "rule")
    @property
    def video_scene_planner_instance(self) -> str: return self._get("video_scene_planner_instance", "scene_planner")
    @property
    def video_animation_planner(self) -> str:   return self._get("video_animation_planner", "rule")
    @property
    def video_animation_planner_instance(self) -> str: return self._get("video_animation_planner_instance", "animation_planner")
    @property
    def video_fps(self) -> int:                 return self._get("video_fps", 30)
    @property
    def video_width(self) -> int:
        resolution = self._get("video_resolution", [1080, 1920])
        return int(resolution[0])
    @property
    def video_height(self) -> int:
        resolution = self._get("video_resolution", [1080, 1920])
        return int(resolution[1])
    @property
    def video_transition(self) -> str:          return self._get("video_transition", "fade")
    @property
    def video_subtitle_font(self) -> str:       return self._get("video_subtitle_font", "SourceHanSans")
    @property
    def video_min_scene_duration(self) -> float:return self._get("video_min_scene_duration", 5.0)
    @property
    def video_max_scene_duration(self) -> float:return self._get("video_max_scene_duration", 8.0)
    @property
    def video_chars_per_second(self) -> float:  return self._get("video_chars_per_second", 4.5)
    @property
    def video_subtitle_max_chars(self) -> int:  return self._get("video_subtitle_max_chars", 20)

    # ---- remotion 段 ----
    @property
    def remotion_planner(self) -> str:          return self._get("remotion_planner", "rule")
    @property
    def remotion_planner_instance(self) -> str: return self._get("remotion_planner_instance", "remotion_designer")
    @property
    def remotion_project_dir(self) -> Path:     return self._resolve_path("remotion_project_dir")
    @property
    def remotion_refine_enabled(self) -> bool:  return self._get("remotion_refine_enabled", False)
    @property
    def remotion_refine_rounds(self) -> int:    return self._get("remotion_refine_rounds", 2)
    @property
    def remotion_reviewer_instance(self) -> str:return self._get("remotion_reviewer_instance", "remotion_reviewer")
    @property
    def remotion_review_frames_per_scene(self) -> int: return self._get("remotion_review_frames_per_scene", 3)

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
