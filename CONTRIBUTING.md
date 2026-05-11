# Contributing / 贡献指南

Thanks for helping improve AI Video Generator.

感谢你参与改进 AI Video Generator。

## Development Setup / 开发环境

Python dependencies are managed with `uv`.

Python 依赖使用 `uv` 管理。

```bash
uv sync
```

Install Node dependencies only for the workspace you need.

只为你需要的 Node 子工程安装依赖。

```bash
cd fronted
npm install

cd ../remotion
npm install
```

## Local Configuration / 本地配置

Copy the example files and fill in your own credentials. Runtime commands read `config/config.yaml`; `.env` is used when present.

复制样例配置，然后填入你自己的密钥。运行命令读取 `config/config.yaml`；`.env` 存在时会被读取。

```bash
cp .env.example .env
cp config/config.example.yaml config/config.yaml
```

Never commit `.env` or `config/config.yaml`.

不要提交 `.env` 或 `config/config.yaml`。

## Useful Commands / 常用命令

Make workflow:

Make 工作流：

```bash
make help
make generate ARGS='--topic "AI workflow"'
make remotion ARGS='--script outputs/scripts/demo.md --title "Demo" --template sketch_course --force'
```

Frontend workflow:

前端工作流：

```bash
uv run python main.py serve --host 0.0.0.0 --port 8000

cd fronted
npm run dev
```

Remotion Studio:

Remotion 预览：

```bash
cd remotion
npm run preview
```

## Pull Requests / PR 要求

- Keep changes focused.
- Do not include generated media, logs, vector DB files, local databases, model caches, or secrets.
- Document new configuration keys in `config/config.example.yaml` and `.env.example`.
- Preserve the HyperFrames sandbox boundary: do not expose arbitrary shell execution to agents or frontend users.

- 保持改动聚焦。
- 不要提交生成媒体、日志、向量库、本地数据库、模型缓存或密钥。
- 新增配置项时，同步更新 `config/config.example.yaml` 和 `.env.example`。
- 保持 HyperFrames 沙盒边界，不要向 Agent 或前端用户暴露任意 shell 执行能力。
