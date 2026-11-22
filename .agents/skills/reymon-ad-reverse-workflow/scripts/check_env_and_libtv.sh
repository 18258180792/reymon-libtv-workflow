#!/usr/bin/env bash
set -euo pipefail

echo "=== 1. 检查 LibTV CLI 可执行文件 ==="
LIBTV_BIN=""
if command -v libtv >/dev/null 2>&1; then
  LIBTV_BIN="$(command -v libtv)"
elif [ -x "$HOME/.libtv/libtv" ]; then
  LIBTV_BIN="$HOME/.libtv/libtv"
fi

if [ -z "$LIBTV_BIN" ]; then
  echo "[未安装] 未检测到 libtv CLI。"
  echo "请在终端执行官方一键安装命令："
  echo "  curl -fsSL https://liblibai-web-static.liblib.cloud/cli/1.1.1/install-libtv-cli.sh | bash"
  exit 1
fi

echo "[已就绪] LibTV CLI 路径: $LIBTV_BIN"
"$LIBTV_BIN" --version || true

echo ""
echo "=== 2. 检查鉴权状态与环境变量 ==="
if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

if [ -n "${LIBTV_ACCESS_KEY:-}" ] && [ "$LIBTV_ACCESS_KEY" != "在此填入你的_LIBTV_ACCESS_KEY" ]; then
  echo "[已配置] 检测到环境变量 LIBTV_ACCESS_KEY"
else
  echo "[提示] 未检测到有效的 .env LIBTV_ACCESS_KEY，尝试检查 libtv CLI 本地登录态..."
fi

"$LIBTV_BIN" account info || {
  echo "[需登录] 请先在终端执行 '~/.libtv/libtv login web' 完成授权，或在项目根目录 .env 中填入 LIBTV_ACCESS_KEY。"
  exit 1
}

echo ""
echo "=== 3. 查询画布当前可用生图模型 (Image Schema) ==="
"$LIBTV_BIN" model search image || true

echo ""
echo "=== 4. 查询画布当前可用视频模型 (Video Schema) ==="
"$LIBTV_BIN" model search video || true
