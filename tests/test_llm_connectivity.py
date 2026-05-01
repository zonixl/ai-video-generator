"""LLM 连通性测试：逐个验证配置中的每个 model instance 是否可用。"""

import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)-5s] %(message)s")
logger = logging.getLogger("llm-test")

TEST_PROMPT = "用一句话介绍Python"
TEST_SYSTEM = "用中文回答"


def test_all():
    from config import Settings
    from core.llm import ModelManager

    cfg = Settings()
    mgr = ModelManager(cfg.models_providers, cfg.models_instances)

    instances = mgr.list_instances()
    logger.info("Testing %d instances: %s", len(instances), instances)
    print()

    results = {}
    for name in instances:
        inst = cfg.models_instances[name]
        provider = inst["provider"]
        model = inst["model"]
        logger.info("[%s] provider=%s model=%s testing ...", name, provider, model)

        t0 = time.time()
        try:
            response = mgr.generate(name, TEST_PROMPT, system_prompt=TEST_SYSTEM)
            elapsed = time.time() - t0
            logger.info("[%s] OK (%.1fs, %d chars)", name, elapsed, len(response))
            logger.info("[%s] response: %s...", name, response[:120].replace("\n", " "))
            results[name] = "OK"
        except Exception as e:
            elapsed = time.time() - t0
            logger.error("[%s] FAIL (%.1fs): %s", name, elapsed, str(e)[:200])
            results[name] = f"FAIL: {e}"

        print()

    # Summary
    logger.info("=" * 50)
    logger.info("Summary:")
    for name, status in results.items():
        icon = "+" if status == "OK" else "x"
        logger.info("  [%s] %s", icon, name)
    ok_count = sum(1 for v in results.values() if v == "OK")
    logger.info("%d/%d instances OK", ok_count, len(results))

    return results


if __name__ == "__main__":
    test_all()
