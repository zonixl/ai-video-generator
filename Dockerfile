# syntax=docker/dockerfile:1.7

FROM node:22-bookworm-slim AS frontend-build
WORKDIR /app/fronted
COPY fronted/package*.json ./
RUN npm ci
COPY fronted/ ./
RUN npm run build

FROM nginx:1.27-alpine AS frontend
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /app/fronted/dist /usr/share/nginx/html
EXPOSE 80

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS backend

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_HTTP_TIMEOUT=300 \
    HF_HOME=/app/data/huggingface \
    TRANSFORMERS_CACHE=/app/data/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/data/sentence-transformers \
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

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY remotion/package*.json ./remotion/
RUN cd remotion && npm ci

COPY . .

RUN mkdir -p outputs logs data

EXPOSE 8000

CMD ["uv", "run", "python", "main.py", "serve", "--host", "0.0.0.0", "--port", "8000"]
