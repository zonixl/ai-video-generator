from faster_whisper import WhisperModel

# 1. 加载模型（第一次会自动下载）
model = WhisperModel("medium", device="cuda", compute_type="float16")

# 2. 转写音频（换成你的文件路径）
segments, info = model.transcribe("test.mp3")

# 3. 输出结果
for segment in segments:
    print(segment.text)
