#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] 未检测到 python3，请先安装 Python 3.9+ 后重试。" >&2
  exit 1
fi

if [ "$#" -eq 0 ]; then
  exec python3 "$SCRIPT_DIR/scripts/setup.py" --init-env --agent all --scope project --check
else
  exec python3 "$SCRIPT_DIR/scripts/setup.py" "$@"
fi
