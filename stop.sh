#!/bin/bash
# 停止并删除 QQBot Docker 容器脚本

echo "==> 停止容器..."
docker stop qqbot

echo "==> 删除容器..."
docker rm qqbot

echo "==> 容器已停止并删除！"
