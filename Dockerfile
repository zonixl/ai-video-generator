# syntax=docker/dockerfile:1.7

FROM node:22-bookworm-slim AS frontend-build
WORKDIR /app/fronted
COPY fronted/package*.json ./
RUN npm ci --cache /tmp/npm-cache \
    && rm -rf /tmp/npm-cache /root/.npm
COPY fronted/ ./
RUN npm run build

FROM nginx:1.27-alpine AS frontend
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /app/fronted/dist /usr/share/nginx/html
EXPOSE 80

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS backend-base

ARG EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_HTTP_TIMEOUT=300 \
    DEFAULT_EMBEDDING_MODEL=${EMBEDDING_MODEL} \
    HF_HOME=/opt/huggingface \
    TRANSFORMERS_CACHE=/opt/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/opt/sentence-transformers \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    CHROME_PATH=/usr/bin/chromium

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        bash \
        curl \
        gnupg \
        ffmpeg \
        chromium \
        fonts-noto-cjk \
        fontconfig \
        git \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

FROM backend-base AS backend-python-cuda
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

FROM backend-base AS backend-python-cpu
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache \
    && (uv pip uninstall torch triton || true) \
    && packages="$(uv pip list --format freeze | sed -n 's/^\(nvidia-[^=]*\)==.*/\1/p')" \
    && if [ -n "$packages" ]; then uv pip uninstall $packages; fi \
    && uv pip install --no-cache --index-url https://download.pytorch.org/whl/cpu torch

FROM backend-base AS backend-runtime
COPY remotion/package*.json ./remotion/
RUN cd remotion \
    && npm ci --cache /tmp/npm-cache \
    && rm -rf /tmp/npm-cache /root/.npm

COPY . .
RUN mkdir -p outputs logs data
EXPOSE 8000
CMD ["/app/.venv/bin/python", "main.py", "serve", "--host", "0.0.0.0", "--port", "8000"]

FROM backend-runtime AS backend-cpu
COPY --from=backend-python-cpu /app/.venv /app/.venv
RUN /app/.venv/bin/python -c "import os; from sentence_transformers import SentenceTransformer; SentenceTransformer(os.environ['DEFAULT_EMBEDDING_MODEL'], device='cpu')"

FROM backend-runtime AS backend-cuda
COPY --from=backend-python-cuda /app/.venv /app/.venv
RUN /app/.venv/bin/python -c "import os; from sentence_transformers import SentenceTransformer; SentenceTransformer(os.environ['DEFAULT_EMBEDDING_MODEL'], device='cpu')"

FROM backend-cpu AS backend
