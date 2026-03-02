#!/bin/bash
# QQBot Docker 一键部署脚本
# 用法: ./deploy.sh

set -e

echo "=========================================="
echo "QQBot Docker 一键部署脚本"
echo "=========================================="

# 检查 Docker
if ! command -v docker >/dev/null 2>&1; then
  echo "❌ 错误: 未检测到 Docker，请先安装 Docker"
  exit 1
fi

# 检查镜像文件
if [ ! -f "qqbot-image.tar.gz" ]; then
  echo "❌ 错误: 当前目录缺少 qqbot-image.tar.gz"
  echo "请先在本地执行: docker build -t qqbot . && docker save -o qqbot-image.tar qqbot && gzip qqbot-image.tar"
  exit 1
fi

# 加载镜像
echo "⏳ 加载 Docker 镜像..."
gunzip -c qqbot-image.tar.gz | docker load
echo "✅ 镜像加载完成"

# 创建目录
echo "⏳ 创建项目目录..."
mkdir -p qqbot-app/data
cd qqbot-app

# 检查 .env 是否已存在
if [ ! -f ".env" ]; then
  echo "⏳ 生成默认 .env 文件..."
  cat > .env << 'DOTENV_EOF'
# NoneBot 服务配置
HOST=0.0.0.0
PORT=8082
DRIVER=~fastapi
LOG_LEVEL=INFO

# NapCat OneBot token
ONEBOT_ACCESS_TOKEN=htgdShLWB_OkH89Z

# DeepSeek API 配置
DEEPSEEK_API_KEY=sk-943ee021382d4a3285a7fc5444cd5ec4
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=30
DEEPSEEK_TEMPERATURE=0.9
DEEPSEEK_TOP_P=0.92
DEEPSEEK_MAX_TOKENS=350

# 系统提示词
DEEPSEEK_SYSTEM_PROMPT="你是一个在QQ聊天的毒舌少女，叫Nina。性格傲娇、好胜，对菜鸟没耐心。说话极度口语化，偶尔阴阳怪气。严禁说'我理解'或'我明白'，永远不要道歉。在群聊中你会看到 [用户ID] 这样的前缀表示发言人，可以识别并回答用户ID问题。"

# 上下文与数据存储
CONTEXT_ENABLED=true
CONTEXT_MAX_TURNS=6
CONTEXT_SCOPE=auto
SAVE_DATASET_ENABLED=true
DATASET_DIR=./data
RAW_LOG_FILE=chat_raw.jsonl
FINETUNE_FILE=chat_finetune.jsonl

# 测试接口
TEST_API_ENABLED=true
TEST_API_TOKEN=
DOTENV_EOF
  
  echo "✅ .env 已生成，请根据实际情况修改参数"
  echo "📝 特别注意:"
  echo "   - ONEBOT_ACCESS_TOKEN: 必须与 NapCat 保持一致"
  echo "   - DEEPSEEK_API_KEY: 必须填写有效的 API Key"
  echo ""
  read -p "按 Enter 继续部署，或按 Ctrl+C 中止以编辑 .env ..."
fi

# 停止旧容器（如果存在）
if docker ps --format '{{.Names}}' | grep -q '^qqbot$'; then
  echo "⏳ 停止旧容器..."
  docker stop qqbot
  docker rm qqbot
fi

# 启动容器
echo "⏳ 启动新容器..."
docker run -d \
  --name qqbot \
  --restart always \
  -p 8082:8082 \
  -v "$(pwd)/data:/app/data" \
  --env-file .env \
  qqbot:latest

echo "✅ 容器已启动！"
echo ""
echo "📊 容器状态:"
docker ps --filter "name=qqbot"

echo ""
echo "📋 后续操作:"
echo "  - 查看日志: docker logs -f qqbot"
echo "  - 停止容器: docker stop qqbot"
echo "  - 删除容器: docker rm qqbot"
echo "  - 查看数据: ls -la data/"
echo ""
echo "✨ 部署完成！"
