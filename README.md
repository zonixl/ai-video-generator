# AI Video Generator

[English](README.md) | [中文](README.zh-CN.md)

AI Video Generator is a local-first AI video generation toolkit for creating short videos from topics, scripts, notes, knowledge-base content, and audio. It combines LLM writing, knowledge retrieval, Whisper speech recognition, Remotion rendering, `sketch_course` templates, and HyperFrames-style technology videos.

Keywords: AI video generator, Remotion video generator, HyperFrames video, AI short video, script to video, knowledge-base video generation, Whisper transcription, local AI video workflow.

## Features

- AI script generation and polishing
- Text and audio ingestion
- Knowledge-base assisted writing
- Remotion video generation
- `sketch_course` mobile-friendly teaching video style
- HyperFrames technology-style video workflow
- Optional TTS, image generation, and video generation providers
- CLI, Makefile, FastAPI backend, and Vite frontend

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Security](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Notices](NOTICE.md)

## Requirements

- Python 3.13+
- `uv`
- Node.js
- FFmpeg
- Chromium, when required by the renderer
- GNU Make, when using `make`

## Install

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

## Configure

`config/config.example.yaml` and `.env.example` are templates.

Create local runtime files:

```bash
cp .env.example .env
cp config/config.example.yaml config/config.yaml
```

The app reads `config/config.yaml` at runtime. Docker Compose also mounts `./config/config.yaml` into the backend container.

The app reads `.env` when it exists. You can also set the same variables through your system environment instead of using `.env`.

Set one default OpenAI-compatible model in `.env`:

```env
DEFAULT_LLM_PROVIDER=default_openai
DEFAULT_LLM_BASE_URL=https://api.openai.com/v1
DEFAULT_LLM_API_KEY=your_api_key
DEFAULT_LLM_MODEL=your_model_name
```

For per-task model routing, edit `models.instances` in `config/config.yaml`.

## Use With Docker

Docker is the easiest way to run the app. The default image is CPU-only and is suitable for most users.

```bash
docker compose up --build
```

Frontend:

```text
http://localhost:8080
```

Backend:

```text
http://localhost:8000
```

Mounted local directories:

```text
./config/config.yaml -> /app/config/config.yaml
./outputs            -> /app/outputs
./logs               -> /app/logs
./data               -> /app/data
```

Hugging Face model downloads use the Docker named volume `hf-cache`.

### Model Downloads And Cache

Knowledge retrieval uses the embedding model configured in `embedding.model_name`. Speech recognition uses the Whisper model configured in `stt.model_size`.

With Docker, the image includes the default embedding model `BAAI/bge-small-zh-v1.5` during build. Whisper speech-recognition models are downloaded at runtime on first use.

Without Docker, `uv sync` installs Python packages only. Embedding and Whisper models are downloaded at runtime on first use, unless they are already available in your local Hugging Face cache.

Runtime Hugging Face downloads are cached and reused:

- Docker: cached in the Docker named volume `hf-cache`
- Local run: cached by Hugging Face in your user cache directory, or in `HF_HOME` if you set it

The default example uses `small` for CPU speech recognition and `medium` for CUDA speech recognition. First use can be slow because the model must be downloaded and loaded.

Set `HF_HUB_OFFLINE=1` only after the required embedding and Whisper models have already been downloaded.

### CUDA Docker

Use the CUDA image only on machines with an NVIDIA GPU, NVIDIA driver, Docker GPU support, and a working `--gpus` runtime.

Verify Docker GPU access first:

```bash
docker run --rm --gpus=all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

Start the CUDA backend:

```bash
docker compose -f docker-compose.yml -f docker-compose.cuda.yml up --build
```

The CUDA compose file uses GPU `0` by default. To select another GPU, set `CUDA_VISIBLE_DEVICES` in `.env`, for example `CUDA_VISIBLE_DEVICES=0,1`.

Enable CUDA in `config/config.yaml` when you want embedding or speech recognition to use the GPU:

```yaml
stt:
  device: "cuda"
  compute_type: "float16"

embedding:
  device: "cuda"
```

## Speech Recognition

The speech recognition module uses `faster-whisper`.

Model names follow the OpenAI Whisper model family:

- `tiny`, `base`, `small`, `medium`, `large`, `turbo`
- English-only variants: `tiny.en`, `base.en`, `small.en`, `medium.en`

CPU configuration:

```yaml
stt:
  model_size: "small"
  device: "cpu"
  compute_type: "int8"
  language: "zh"

embedding:
  device: "cpu"
```

CUDA configuration:

```yaml
stt:
  model_size: "medium"
  device: "cuda"
  compute_type: "float16"
  language: "zh"

embedding:
  device: "cuda"
```

The model must be available before using audio ingestion. Use an existing local/cache model, or enable online model download in your environment before running the audio ingestion command.

Whisper model reference: [openai/whisper](https://github.com/openai/whisper#available-models-and-languages).

When using Docker for the first time, missing Hugging Face models are downloaded automatically. Whisper models are cached in the Docker named volume `hf-cache`.

Speech recognition can be slow. The first run may spend several minutes downloading the Whisper model. Larger models such as `medium` and `large` are slower to download and run. CPU mode is slower than CUDA mode; use the CUDA Docker command when you want GPU acceleration.

To run with local cached models only, set:

```env
HF_HUB_OFFLINE=1
```

## Knowledge Retrieval

Knowledge-base retrieval uses the embedding model configured in `embedding.model_name`. The Docker backend image includes the default `BAAI/bge-small-zh-v1.5` embedding model.

If you change `embedding.model_name`, the new model is downloaded on first use. Docker caches it in `hf-cache`; local runs cache it in the Hugging Face user cache or `HF_HOME`.

## Use With Make

```bash
make help
```

Generate a script:

```bash
make generate ARGS='--topic "AI workflow" --style "short video"'
```

Generate a `sketch_course` Remotion video:

```bash
make remotion ARGS='--script outputs/scripts/demo.md --title "Demo" --template sketch_course --force'
```

Generate HyperFrames files:

```bash
make hyperframes ARGS='--script outputs/hf_demo.txt --title "AI Workflow" --duration 10 --ratio 9:16 --style tech_hud --no-render'
```

## Use With Frontend

Start the backend:

```bash
uv run python main.py serve --host 0.0.0.0 --port 8000
```

Start the frontend:

```bash
cd fronted
npm run dev
```

Open the URL printed by Vite.

## Direct CLI

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

## License

MIT. See [LICENSE](LICENSE).
