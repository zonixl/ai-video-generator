# AI Video Generator

[English](README.md) | [中文](README.zh-CN.md)

AI Video Generator 是一个本地优先的 AI 视频生成工具，可以把选题、脚本、笔记、知识库内容和音频转成短视频素材、Remotion 视频、`sketch_course` 教学视频，以及 HyperFrames 风格的科技感视频。

关键词：AI 视频生成器、Remotion 视频生成、HyperFrames 视频、AI 短视频、文案转视频、知识库视频生成、Whisper 语音识别、本地 AI 视频工作流。

## 功能

- AI 脚本生成和润色
- 文本和音频导入
- 知识库辅助写作
- Remotion 视频生成
- `sketch_course` 手机友好的教学视频风格
- HyperFrames 科技感视频流程
- 可选 TTS、图片生成和视频生成服务
- CLI、Makefile、FastAPI 后端和 Vite 前端

## 演示

演示视频见 [examples/](examples/)。

## 文档

- [架构](docs/ARCHITECTURE.zh-CN.md)
- [安全](SECURITY.md)
- [贡献](CONTRIBUTING.md)
- [声明](NOTICE.md)

## 环境要求

- Python 3.13+
- `uv`
- Node.js
- FFmpeg
- 渲染器需要时安装 Chromium
- 使用 `make` 时需要 GNU Make

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

```bash
npm install -g hyperframes
```

## 配置

`config/config.example.yaml` 和 `.env.example` 是模板文件。

创建本地运行配置：

```bash
cp .env.example .env
cp config/config.example.yaml config/config.yaml
```

程序运行时读取 `config/config.yaml`。Docker Compose 会把 `./config/config.yaml` 挂载到后端容器里。

程序会在 `.env` 存在时读取它。你也可以直接使用系统环境变量。

在 `.env` 中配置一个默认 OpenAI-compatible 模型：

```env
DEFAULT_LLM_PROVIDER=default_openai
DEFAULT_LLM_BASE_URL=https://api.openai.com/v1
DEFAULT_LLM_API_KEY=your_api_key
DEFAULT_LLM_MODEL=your_model_name
```

如果要给不同任务配置不同模型，修改 `config/config.yaml` 里的 `models.instances`。

图片生成默认使用 `doubao-seedream-4-5-251128`（火山引擎 Ark API），在 `.env` 中设置 `ARK_API_KEY` 即可启用。如需使用其他图片生成服务，修改 `config/config.yaml` 中的 `image_gen` 配置。

## 使用 Docker

Docker 是最简单的启动方式。默认镜像使用 CPU，适合大多数用户。

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

Hugging Face 模型下载会使用 Docker named volume `hf-cache`。

### 模型下载和缓存

知识库检索使用 `embedding.model_name` 配置的 embedding 模型。语音识别使用 `stt.model_size` 配置的 Whisper 模型。

使用 Docker 时，镜像在构建阶段已经包含默认 embedding 模型 `BAAI/bge-small-zh-v1.5`。Whisper 语音识别模型会在首次使用语音识别时下载。

不使用 Docker 时，`uv sync` 只安装 Python 依赖。embedding 和 Whisper 模型都会在首次使用时下载，除非你的本地 Hugging Face 缓存中已经有对应模型。

运行时下载的 Hugging Face 模型会被缓存并复用：

- Docker：缓存到 Docker named volume `hf-cache`
- 本地直接运行：缓存到 Hugging Face 用户缓存目录，或者你设置的 `HF_HOME`

默认示例中，CPU 语音识别使用 `small`，CUDA 语音识别使用 `medium`。首次使用会比较慢，因为需要下载并加载模型。

只有在需要的 embedding 和 Whisper 模型都已经下载完成后，再设置 `HF_HUB_OFFLINE=1`。

### CUDA Docker

只有在机器有 NVIDIA GPU、NVIDIA 驱动、Docker GPU 支持，并且 `--gpus` 运行时可用时，才使用 CUDA 镜像。

先验证 Docker 是否能访问 GPU：

```bash
docker run --rm --gpus=all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

启动 CUDA 后端：

```bash
docker compose -f docker-compose.yml -f docker-compose.cuda.yml up --build
```

CUDA compose 默认使用第 0 张 GPU。需要选择其他 GPU 时，在 `.env` 中设置 `CUDA_VISIBLE_DEVICES`，例如 `CUDA_VISIBLE_DEVICES=0,1`。

如果要让 embedding 或语音识别使用 GPU，在 `config/config.yaml` 中启用 CUDA：

```yaml
stt:
  device: "cuda"
  compute_type: "float16"

embedding:
  device: "cuda"
```

## 语音识别

语音识别模块使用 `faster-whisper`。

模型名称参考 OpenAI Whisper 模型系列：

- `tiny`、`base`、`small`、`medium`、`large`、`turbo`
- 英文模型：`tiny.en`、`base.en`、`small.en`、`medium.en`

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

使用音频导入前，需要模型已经可用。可以使用本地模型或缓存模型，也可以在运行环境中开启在线模型下载。

Whisper 模型参考：[openai/whisper](https://github.com/openai/whisper#available-models-and-languages)。

Docker 首次使用时，如果缺少 Hugging Face 模型，会自动下载。Whisper 模型会缓存到 Docker named volume `hf-cache`。

语音识别速度会比较慢。首次运行可能需要几分钟下载 Whisper 模型。`medium`、`large` 这类大模型下载和识别都会更慢。CPU 模式比 CUDA 模式慢；需要 GPU 加速时，使用 CUDA Docker 启动命令。

如果只想使用本地缓存模型，设置：

```env
HF_HUB_OFFLINE=1
```

## 知识库检索

知识库检索使用 `embedding.model_name` 配置的 embedding 模型。Docker 后端镜像包含默认的 `BAAI/bge-small-zh-v1.5` embedding 模型。

如果修改了 `embedding.model_name`，新模型会在首次使用时下载。Docker 会缓存到 `hf-cache`；本地直接运行会缓存到 Hugging Face 用户缓存目录或 `HF_HOME`。

## 使用 Make

```bash
make help
```

生成脚本：

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

## 致谢

本项目使用了以下开源项目：

- [HyperFrames](https://github.com/heygen-com/hyperframes) — AI 驱动的动画视频生成工具，由 HeyGen 开源

## License

MIT. See [LICENSE](LICENSE).
