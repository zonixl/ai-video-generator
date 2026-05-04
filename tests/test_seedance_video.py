"""Seedance 视频生成 API 测试 — 直接修改下方参数运行即可。"""

import base64
import json
import time
from pathlib import Path

import requests

# ============================================================
#  在下面改参数
# ============================================================
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
API_KEY = "ark-5ce8304e-595f-44b9-82e9-9dd3d49a3ec5-0c63e"
MODEL = "doubao-seedance-1-5-pro-251215"

IMAGE_PATH = r"E:\PycharmProjects\my_project\outputs\videos\video-20260504-111741\images\44444.jpg"  # 首帧图片
PROMPT = "根据视频内容反推完整视频提示词，必须涵盖以下要素： 主体（人物/物品/场景）：详细描述核心对象特征 动作：精确说明动态表现 ，详细动作分解 ，包括身体细微动作，头部细微动作手部细微动作，脸部细微动作，腿部细微动作，眼神细微动作，嘴巴细微动作，身材细节，衣服飘动动作细节，要求百分之百还原  场景：环境、纷围、时间设定 光影：光线类型、强度、方向 运镜：推/拉/摇/移/俯拍/仰拍等镜头语言 风格：视觉风格、色调等 画质：分辨率、帧率、特效参数，着重描写人物的妆造，发型，神态，服饰，最后都统一加上画面内容无字幕，人物无纹身的提示"
RESOLUTION = "480p"
RATIO = "9:16"
DURATION = 10
GENERATE_AUDIO = True

OUTPUT_DIR = Path("outputs/test_seedance")
POLL_INTERVAL = 5  # 轮询间隔（秒）
TIMEOUT = 300      # 超时（秒）
# ============================================================


def encode_image(path):
    p = Path(path)
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp"}.get(p.suffix.lower(), "image/png")
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 创建任务
    print(f"[1/3] 创建任务: {IMAGE_PATH}")
    image_b64 = encode_image(IMAGE_PATH)
    body = {
        "model": MODEL,
        "content": [
            {"type": "image_url", "image_url": {"url": image_b64}, "role": "first_frame"},
            {"type": "text", "text": PROMPT},
        ],
        "resolution": RESOLUTION,
        "ratio": RATIO,
        "duration": DURATION,
        "generate_audio": GENERATE_AUDIO,
        "watermark": False,
    }
    resp = requests.post(
        f"{BASE_URL}/contents/generations/tasks",
        json=body,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        timeout=30,
    )
    print(f"    HTTP {resp.status_code}")
    if resp.status_code != 200:
        print(f"    ERROR: {resp.text[:500]}")
        return
    data = resp.json()
    task_id = data["id"]
    print(f"    task_id: {task_id}")

    # 2. 轮询
    print(f"[2/3] 轮询中 (interval={POLL_INTERVAL}s, timeout={TIMEOUT}s) ...")
    t0 = time.time()
    while time.time() - t0 < TIMEOUT:
        time.sleep(POLL_INTERVAL)
        resp = requests.get(
            f"{BASE_URL}/contents/generations/tasks/{task_id}",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30,
        )
        if resp.status_code != 200:
            print(f"    poll HTTP {resp.status_code}")
            continue
        result = resp.json()
        status = result.get("status", "")
        elapsed = time.time() - t0
        print(f"    {status} ({elapsed:.0f}s)")

        if status == "succeeded":
            video_url = result.get("content", {}).get("video_url", "")
            print(f"    video_url: {video_url}")
            break
        if status == "failed":
            print(f"    FAILED: {result.get('error', {})}")
            return
    else:
        print("    TIMEOUT!")
        return

    # 3. 下载
    out_path = OUTPUT_DIR / f"seedance_{task_id[:8]}.mp4"
    print(f"[3/3] 下载: {out_path}")
    resp = requests.get(video_url, timeout=TIMEOUT)
    out_path.write_bytes(resp.content)
    print(f"    {len(resp.content) / 1024 / 1024:.1f}MB saved")

    # 保存响应详情
    meta_path = OUTPUT_DIR / f"seedance_{task_id[:8]}.json"
    meta_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    meta: {meta_path}")
    print("DONE")


if __name__ == "__main__":
    main()
