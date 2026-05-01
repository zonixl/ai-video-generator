"""LLM模块测试。"""

import pytest


@pytest.mark.skip(reason="需要Ollama服务运行，仅手动执行")
def test_ollama_provider():
    from core.llm import OllamaProvider
    provider = OllamaProvider()
    result = provider.generate(
        model="qwen2.5:3b",
        prompt="用一句话介绍Python",
        system_prompt="用中文回答",
        temperature=0.3,
        max_tokens=100,
    )
    assert len(result) > 0


@pytest.mark.skip(reason="需要Ollama服务运行，仅手动执行")
def test_model_manager():
    from core.llm import ModelManager

    providers = {
        "ollama": {"type": "ollama", "base_url": "http://localhost:11434"},
    }
    instances = {
        "test_chat": {"provider": "ollama", "model": "qwen2.5:3b",
                      "temperature": 0.3, "max_tokens": 100},
    }
    mgr = ModelManager(providers, instances)
    result = mgr.generate("test_chat", "Python是什么", system_prompt="一句话回答")
    assert len(result) > 0
    assert "test_chat" in mgr.list_instances()


def test_model_manager_config_parsing():
    """测试配置解析（不需要真实服务）。"""
    from config import Settings
    import os

    # 临时清除可能的环境变量
    old_key = os.environ.pop("DEEPSEEK_API_KEY", None)
    try:
        cfg = Settings()
        providers = cfg.models_providers
        instances = cfg.models_instances

        assert "ollama" in providers
        assert providers["ollama"]["type"] == "ollama"
        assert "script_writer" in instances
        assert "polisher" in instances
        assert "provider" in instances["script_writer"]
        assert "model" in instances["script_writer"]
    finally:
        if old_key is not None:
            os.environ["DEEPSEEK_API_KEY"] = old_key
