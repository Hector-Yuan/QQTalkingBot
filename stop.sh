#!/bin/bash
# 停止并删除 QQBot Docker 容器脚本

set -e

CONTAINER_NAME="${CONTAINER_NAME:-qqbot}"

echo "==> 停止容器..."
docker stop "$CONTAINER_NAME" 2>/dev/null || true

echo "==> 删除容器..."
docker rm "$CONTAINER_NAME" 2>/dev/null || true

echo "==> 容器已停止并删除！"
