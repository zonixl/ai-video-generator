"""MiMo TTS 风格对比测试 — 生成各风格音频到 test_tts/ 目录。

用法：python tests/test_tts_styles.py
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml
from core.tts import MiMoProvider, MIMO_STYLES


# ---- 从 config.yaml 读取配置 ----
CONFIG_PATH = ROOT / "config" / "config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    _cfg = yaml.safe_load(f)

_tts_cfg = _cfg.get("tts", {})
_mimo_cfg = _tts_cfg.get("mimo", {})
VOICE = _tts_cfg.get("voice", "冰糖")
RATE = float(_tts_cfg.get("speed", 1.0))
BASE_URL = _mimo_cfg.get("base_url", "https://api.xiaomimimo.com/v1")
API_KEY = _mimo_cfg.get("api_key", "")
MODEL = _mimo_cfg.get("model", "mimo-v2.5-tts")

# ---- 测试文本 ----
TEST_TEXT = "人工智能正在改变我们的生活方式，从医疗诊断到自动驾驶，每一个领域都在经历深刻的变革。未来十年，这场技术革命将彻底重塑人类社会的面貌。"

OUTPUT_DIR = ROOT / "test_tts"


def main():
    if not API_KEY:
        print("ERROR: tts.mimo.api_key 未配置，请检查 config/config.yaml")
        sys.exit(1)

    provider = MiMoProvider(base_url=BASE_URL, api_key=API_KEY, model=MODEL)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Voice: {VOICE}  Rate: {RATE}  Model: {MODEL}")
    print(f"Text: {TEST_TEXT}")
    print(f"Output: {OUTPUT_DIR}/")
    print("=" * 60)

    for emotion in MIMO_STYLES:
        out_path = OUTPUT_DIR / f"tts_{emotion}.mp3"
        print(f"\n[{emotion}]")
        print(f"  Style: {MIMO_STYLES[emotion]}")
        t0 = time.perf_counter()
        try:
            asset = provider.synthesize(
                TEST_TEXT, out_path,
                voice=VOICE, rate=RATE, emotion=emotion,
            )
            elapsed = time.perf_counter() - t0
            print(f"  OK  duration={asset.duration:.1f}s  elapsed={elapsed:.1f}s  -> {out_path.name}")
        except Exception as exc:
            elapsed = time.perf_counter() - t0
            print(f"  FAILED  {exc}  elapsed={elapsed:.1f}s")

    # 额外：无风格（默认）
    print(f"\n[default]")
    out_path = OUTPUT_DIR / "tts_default.mp3"
    t0 = time.perf_counter()
    try:
        asset = provider.synthesize(
            TEST_TEXT, out_path,
            voice=VOICE, rate=RATE, emotion="",
        )
        elapsed = time.perf_counter() - t0
        print(f"  OK  duration={asset.duration:.1f}s  elapsed={elapsed:.1f}s  -> {out_path.name}")
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        print(f"  FAILED  {exc}  elapsed={elapsed:.1f}s")

    print("\n" + "=" * 60)
    print(f"Done. {len(list(OUTPUT_DIR.glob('*.mp3')))} files in {OUTPUT_DIR}/")
    print("请逐个播放对比：语速是否一致、语气差异是否明显、有没有多余内容。")


if __name__ == "__main__":
    main()
