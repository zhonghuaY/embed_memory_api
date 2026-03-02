#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 加载配置
if [ -f config.env ]; then
    set -a
    source config.env
    set +a
fi

EMBED_HOST="${EMBED_HOST:-0.0.0.0}"
EMBED_PORT="${EMBED_PORT:-8786}"

# 如果有 venv 则激活
if [ -d .venv ]; then
    source .venv/bin/activate
fi

echo "Starting Embedding API on ${EMBED_HOST}:${EMBED_PORT}"
exec python3 main.py
