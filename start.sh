#!/bin/bash
# 启动 QQBot Docker 容器脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "错误: 未检测到 docker，请先安装 Docker。"
  exit 1
fi

if [ ! -f .env ]; then
  echo "错误: 当前目录缺少 .env 文件。"
  exit 1
fi

PORT="${PORT:-8082}"
CONTAINER_NAME="${CONTAINER_NAME:-qqbot}"
IMAGE_NAME="${IMAGE_NAME:-qqbot}"

echo "==> 构建 Docker 镜像..."
docker build -t "$IMAGE_NAME" .

echo "==> 停止并删除旧容器（如果存在）..."
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true

echo "==> 启动新容器..."
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart always \
  -p "$PORT:$PORT" \
  -v "$SCRIPT_DIR/data:/app/data" \
  --env-file .env \
  "$IMAGE_NAME"

echo "==> 容器已启动！"
echo "查看日志: docker logs -f $CONTAINER_NAME"
echo "停止容器: ./stop.sh"
