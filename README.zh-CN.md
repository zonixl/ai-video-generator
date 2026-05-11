# AI Content Pipeline

[English](README.md) | [中文](README.zh-CN.md)

AI Content Pipeline 是一个本地优先的 AI 内容生产工具。它可以把选题、文案、笔记和音频转成脚本、知识库内容、短视频素材、Remotion 视频，以及 HyperFrames 风格的科技感视频。

## 功能

- 文案生成和润色
- 文本和音频摄入
- 知识库辅助写作
- Remotion 视频生成
- `sketch_course` 手机友好的教学视频风格
- HyperFrames 科技感视频工作流
- 可选 TTS、图片生成、视频生成供应商
- CLI、Makefile、FastAPI 后端、Vite 前端

## 文档

- [架构](docs/ARCHITECTURE.zh-CN.md)
- [安全](SECURITY.md)
- [贡献](CONTRIBUTING.md)
- [第三方声明](NOTICE.md)

## 环境要求

- Python 3.13+
- `uv`
- Node.js
- FFmpeg
- 渲染器需要时安装 Chromium
- 使用 `make` 时安装 GNU Make

## 安装

```bash
uv sync
```

```bash
cd fronted
npm install
```

```bash
cd remotion
npm install
```

## 配置

```bash
cp .env.example .env
cp config/config.example.yaml config/config.yaml
```

在 `.env` 中配置一个默认 OpenAI 兼容模型：

```env
DEFAULT_LLM_PROVIDER=default_openai
DEFAULT_LLM_BASE_URL=https://api.openai.com/v1
DEFAULT_LLM_API_KEY=your_api_key
DEFAULT_LLM_MODEL=your_model_name
```

如果要为不同任务配置不同模型，修改 `config/config.yaml` 里的 `models.instances`。

## 使用 Docker

```bash
docker compose up --build
```

前端：

```text
http://localhost:8080
```

后端：

```text
http://localhost:8000
```

本地挂载目录：

```text
./config/config.yaml -> /app/config/config.yaml
./outputs            -> /app/outputs
./logs               -> /app/logs
./data               -> /app/data
```

## 语音识别

语音识别模块使用 `faster-whisper`。

模型名称参考 OpenAI Whisper 模型系列：

- `tiny`、`base`、`small`、`medium`、`large`、`turbo`
- 英文专用版本：`tiny.en`、`base.en`、`small.en`、`medium.en`

CPU 配置：

```yaml
stt:
  model_size: "small"
  device: "cpu"
  compute_type: "int8"
  language: "zh"

embedding:
  device: "cpu"
```

CUDA 配置：

```yaml
stt:
  model_size: "medium"
  device: "cuda"
  compute_type: "float16"
  language: "zh"

embedding:
  device: "cuda"
```

使用音频摄入前，需要先让模型在本地或缓存中可用，也可以在运行音频摄入前打开环境中的在线模型下载。

Whisper 模型参考：[openai/whisper](https://github.com/openai/whisper#available-models-and-languages)。

## 使用 Make

```bash
make help
```

生成文案：

```bash
make generate ARGS='--topic "AI workflow" --style "short video"'
```

生成 `sketch_course` Remotion 视频：

```bash
make remotion ARGS='--script outputs/scripts/demo.md --title "Demo" --template sketch_course --force'
```

生成 HyperFrames 文件：

```bash
make hyperframes ARGS='--script outputs/hf_demo.txt --title "AI Workflow" --duration 10 --ratio 9:16 --style tech_hud --no-render'
```

## 使用前端

启动后端：

```bash
uv run python main.py serve --host 0.0.0.0 --port 8000
```

启动前端：

```bash
cd fronted
npm run dev
```

打开 Vite 输出的地址。

## 直接使用 CLI

```bash
uv run python main.py --help
```

```bash
uv run python main.py produce-remotion --script outputs/scripts/demo.md --title "Demo" --template sketch_course --force
```

```bash
uv run python main.py produce-hyperframes --script outputs/hf_demo.txt --title "AI Workflow" --duration 10 --ratio 9:16 --style tech_hud --no-render
```

## Remotion Studio

```bash
cd remotion
npm run preview
```

## 许可证

MIT。见 [LICENSE](LICENSE)。
