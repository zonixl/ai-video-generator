# Architecture

[English](ARCHITECTURE.md) | [中文](ARCHITECTURE.zh-CN.md)

## Overview

```mermaid
flowchart LR
  User["User"] --> Frontend["Vite frontend"]
  User --> CLI["CLI / Makefile"]
  Frontend --> API["FastAPI backend"]
  CLI --> Main["main.py"]
  API --> Main
  Main --> Pipeline["pipeline/"]
  Pipeline --> Core["core/"]
  Core --> Models["LLM providers"]
  Core --> STT["faster-whisper"]
  Core --> TTS["TTS providers"]
  Core --> Remotion["Remotion renderer"]
  Core --> HyperFrames["HyperFrames sandbox workflow"]
  Pipeline --> Outputs["outputs/"]
```

## Main Parts

- `main.py`: CLI commands and backend command handlers
- `api/`: FastAPI routes, job APIs, and request schemas
- `fronted/`: Vite frontend
- `pipeline/`: end-to-end production workflows
- `core/`: model providers, planners, renderers, prompts, sandbox tools
- `remotion/`: Remotion project and templates
- `config/`: YAML settings and environment variable loading
- `outputs/`: generated scripts, plans, media, subtitles, and rendered files

## Video Workflows

- Remotion: script -> scene plan -> Remotion input -> render
- `sketch_course`: script -> sketch-style course plan -> mobile-friendly Remotion render
- HyperFrames: script -> sandbox files -> optional preview -> optional render

## Configuration Flow

```mermaid
flowchart LR
  Env[".env"] --> Settings["config/settings.py"]
  Yaml["config/config.yaml"] --> Settings
  Settings --> Models["models.providers + models.instances"]
  Settings --> Pipelines["pipelines"]
```

`models.providers` defines available model endpoints. `models.instances` maps each task to a provider and model.
