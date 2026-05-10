"""MiMo TTS 风格对比测试 — 生成各风格音频到 test_tts/ 目录。

用法：python tests/test_tts_styles.py
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml
from core.tts import MiMoProvider


# ---- 从 config.yaml 读取配置 ----
CONFIG_PATH = ROOT / "config" / "config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    _cfg = yaml.safe_load(f)

_tts_cfg = _cfg.get("tts", {})
_mimo_cfg = _tts_cfg.get("mimo", {})
VOICE = _tts_cfg.get("voice", "苏打")
BASE_URL = _mimo_cfg.get("base_url", "https://api.xiaomimimo.com/v1")
API_KEY = _mimo_cfg.get("api_key", "")
MODEL = _mimo_cfg.get("model", "mimo-v2.5-tts")

# ---- 测试文本 ----
TEST_TEXT = "给你一个马上就能用的方法：找个你最亲近的人，对着她讲课。这比自己默读有效十倍。"

OUTPUT_DIR = ROOT / "test_tts"

EMOTIONS = [
    "叙事平缓",
    "自信坚定",
    "温柔亲切",
    "娓娓道来",
    "严肃沉稳",
    "兴奋激动",
]


def main():
    if not API_KEY:
        print("ERROR: tts.mimo.api_key 未配置，请检查 config/config.yaml")
        sys.exit(1)

    provider = MiMoProvider(base_url=BASE_URL, api_key=API_KEY, model=MODEL)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Voice: {VOICE}  Model: {MODEL}")
    print(f"Text: {TEST_TEXT}")
    print(f"Output: {OUTPUT_DIR}/")
    print("=" * 60)

    # ---- 1. 各情绪风格（默认无 audio tag） ----
    print("\n--- 各情绪风格 (use_audio_tag=False) ---")
    for emotion in EMOTIONS:
        out_path = OUTPUT_DIR / f"tts_{emotion}.mp3"
        t0 = time.perf_counter()
        try:
            asset = provider.synthesize(
                TEST_TEXT, out_path,
                voice=VOICE, emotion=emotion,
            )
            elapsed = time.perf_counter() - t0
            print(f"  {emotion:8s}  OK  duration={asset.duration:.1f}s  elapsed={elapsed:.1f}s  -> {out_path.name}")
        except Exception as exc:
            elapsed = time.perf_counter() - t0
            print(f"  {emotion:8s}  FAILED  {exc}  elapsed={elapsed:.1f}s")

    # ---- 2. 带 audio tag 对比 ----
    print("\n--- audio tag 对比 (叙事平缓) ---")
    for use_tag, label in [(False, "no_tag"), (True, "with_tag")]:
        out_path = OUTPUT_DIR / f"tts_tag_{label}.mp3"
        t0 = time.perf_counter()
        try:
            asset = provider.synthesize(
                TEST_TEXT, out_path,
                voice=VOICE, emotion="叙事平缓",
                use_audio_tag=use_tag,
            )
            elapsed = time.perf_counter() - t0
            print(f"  {label:10s}  OK  duration={asset.duration:.1f}s  elapsed={elapsed:.1f}s  -> {out_path.name}")
        except Exception as exc:
            elapsed = time.perf_counter() - t0
            print(f"  {label:10s}  FAILED  {exc}  elapsed={elapsed:.1f}s")

    # ---- 3. normalize_tts_text 效果对比 ----
    print("\n--- normalize_tts_text 效果 ---")
    tech_text = "用AI和API做TTS，比RAG简单。OpenAI的GPT很强。"
    raw_out = OUTPUT_DIR / "tts_tech_normalized.mp3"
    t0 = time.perf_counter()
    try:
        asset = provider.synthesize(
            tech_text, raw_out,
            voice=VOICE, emotion="叙事平缓",
        )
        elapsed = time.perf_counter() - t0
        print(f"  tech_text(normalized)  OK  duration={asset.duration:.1f}s  elapsed={elapsed:.1f}s  -> {raw_out.name}")
        print(f"    原文: {tech_text}")
        print(f"    规范: {MiMoProvider.normalize_tts_text(tech_text)}")
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        print(f"  tech_text  FAILED  {exc}  elapsed={elapsed:.1f}s")

    # ---- 4. build_voice_prompt 输出预览 ----
    print("\n--- build_voice_prompt 预览 ---")
    for emotion in ["叙事平缓", "兴奋激动"]:
        prompt, assistant = provider.build_voice_prompt(
            TEST_TEXT, emotion=emotion, use_audio_tag=False,
        )
        print(f"\n  [{emotion}] assistant_text:")
        print(f"    {assistant[:80]}...")
        print(f"  [{emotion}] voice_prompt 末尾:")
        print(f"    ...{prompt[-100:]}")

    print("\n" + "=" * 60)
    mp3_count = len(list(OUTPUT_DIR.glob("*.mp3")))
    print(f"Done. {mp3_count} files in {OUTPUT_DIR}/")
    print("请逐个播放对比：自然度、情绪差异、是否有表演感。")


if __name__ == "__main__":
    main()
