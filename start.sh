#!/bin/bash
# 启动 QQBot Docker 容器脚本

set -e

echo "==> 构建 Docker 镜像..."
docker build -t qqbot .

echo "==> 停止并删除旧容器（如果存在）..."
docker stop qqbot 2>/dev/null || true
docker rm qqbot 2>/dev/null || true

echo "==> 启动新容器..."
docker run -d \
  --name qqbot \
  --restart always \
  -p 8082:8082 \
  -v "$(pwd)/data:/app/data" \
  --env-file .env \
  qqbot

echo "==> 容器已启动！"
echo "查看日志: docker logs -f qqbot"
echo "停止容器: ./stop.sh"
