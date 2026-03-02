#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="embed-api"
SERVICE_FILE="${SCRIPT_DIR}/${SERVICE_NAME}.service"

echo "=== Embedding API Service Installer ==="

if [ ! -f "$SERVICE_FILE" ]; then
    echo "ERROR: ${SERVICE_FILE} not found"
    exit 1
fi

if [ ! -d "${SCRIPT_DIR}/.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "${SCRIPT_DIR}/.venv"
    "${SCRIPT_DIR}/.venv/bin/pip" install -r "${SCRIPT_DIR}/requirements.txt"
fi

echo "Installing systemd user service..."
mkdir -p ~/.config/systemd/user
cp "$SERVICE_FILE" ~/.config/systemd/user/${SERVICE_NAME}.service
systemctl --user daemon-reload
systemctl --user enable ${SERVICE_NAME}

# 先清理可能占用端口的旧进程
lsof -ti:8786 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1

systemctl --user start ${SERVICE_NAME}

# 允许用户服务在未登录时运行（开机自启需要）
loginctl enable-linger "$(whoami)" 2>/dev/null || echo "WARNING: loginctl enable-linger failed, may need sudo"

echo ""
echo "Service installed and started."
echo "  Status:  systemctl --user status ${SERVICE_NAME}"
echo "  Logs:    journalctl --user -u ${SERVICE_NAME} -f"
echo "  Stop:    systemctl --user stop ${SERVICE_NAME}"
echo "  Restart: systemctl --user restart ${SERVICE_NAME}"
