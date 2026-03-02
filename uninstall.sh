#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="embed-api"

echo "=== Embedding API Service Uninstaller ==="

systemctl --user stop ${SERVICE_NAME} 2>/dev/null || true
systemctl --user disable ${SERVICE_NAME} 2>/dev/null || true
rm -f ~/.config/systemd/user/${SERVICE_NAME}.service
systemctl --user daemon-reload

echo "Service removed."
