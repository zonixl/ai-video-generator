# Security Policy / 安全策略

## Secrets / 密钥

Do not commit credentials or local configuration.

不要提交任何密钥或本地配置。

Never commit:

不要提交：

- `.env`
- `config/config.yaml`
- API keys, JWTs, bearer tokens, cookies, or private endpoints
- generated media, logs, local databases, vector stores, and model caches

Use `config/config.example.yaml` and `.env.example` as public templates.

公开配置请使用 `config/config.example.yaml` 和 `.env.example`。

## Model And Agent Safety / 模型与 Agent 安全

The HyperFrames agent workflow is designed to write only inside a sandboxed job directory. Agent tools must validate paths and must not expose arbitrary shell execution.

HyperFrames Agent 工作流设计为只能写入受限的任务沙盒目录。Agent 工具必须校验路径，不能暴露任意 shell 执行能力。

Do not add tools that allow an agent or frontend user to:

不要新增允许 Agent 或前端用户执行以下行为的工具：

- read arbitrary files outside the project or sandbox
- write arbitrary files outside the sandbox
- run shell commands
- delete project files
- access `.env`, package manifests, lockfiles, or private config

- 读取项目或沙盒外的任意文件
- 写入沙盒外的任意文件
- 执行 shell 命令
- 删除项目文件
- 访问 `.env`、包描述文件、锁文件或私有配置

## Reporting / 报告问题

If you find a security issue, please open a private report if the hosting platform supports it. Otherwise, open a minimal public issue without secrets or exploit details.

如果你发现安全问题，请优先使用托管平台的私密报告能力。如果没有，请提交最小化公开 issue，不要包含密钥或完整利用细节。
