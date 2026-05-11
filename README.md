# AI Content Pipeline

[English](README.md) | [中文](README.zh-CN.md)

AI Content Pipeline is a local-first AI content production toolkit. It turns topics, scripts, notes, and audio into scripts, knowledge-base content, short-video assets, Remotion videos, and HyperFrames-style technology videos.

## Features

- Script generation and polishing
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

```bash
cp .env.example .env
cp config/config.example.yaml config/config.yaml
```

Set one default OpenAI-compatible model in `.env`:

```env
DEFAULT_LLM_PROVIDER=default_openai
DEFAULT_LLM_BASE_URL=https://api.openai.com/v1
DEFAULT_LLM_API_KEY=your_api_key
DEFAULT_LLM_MODEL=your_model_name
```

For per-task model routing, edit `models.instances` in `config/config.yaml`.

## Use With Docker

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
