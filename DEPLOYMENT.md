# 轻量级 Docker 部署指南

## 快速开始（3 步）

### 1️⃣ 本地构建镜像（Windows）

在项目目录执行：

```powershell
# 给脚本执行权限（首次需要）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 构建并打包镜像
.\build-image.ps1
```

生成文件：`qqbot-image.tar.gz` （约 300-500MB）

### 2️⃣ 上传到服务器

```bash
# 方式 A: 用 scp（推荐）
scp qqbot-image.tar.gz root@116.62.130.37:/root/

# 方式 B: 用阿里云工作台 / Web Terminal 上传文件
# 或用 Alibaba Cloud CLI: aliyun ecs SendFile
```

### 3️⃣ 服务器一键部署

```bash
ssh root@116.62.130.37

cd /root

# 下载部署脚本（或直接上传 deploy.sh）
wget https://raw.githubusercontent.com/Hector-Yuan/QQTalkingBot/main/deploy.sh
chmod +x deploy.sh

# 执行部署（自动加载镜像、创建目录、启动容器）
./deploy.sh
```

脚本会提示你编辑 `.env` 文件，确保以下项正确：
- `HOST=0.0.0.0`（必须）
- `PORT=8082`
- `ONEBOT_ACCESS_TOKEN` 与 NapCat 一致
- `DEEPSEEK_API_KEY` 有效

---

## 后续操作

### 查看日志
```bash
docker logs -f qqbot
```

### 测试接口
```bash
curl -X POST "http://127.0.0.1:8082/dev/chat" \
  -H "Content-Type: application/json" \
  -H "X-Test-Token: your_token" \
  -d '{"text":"你好","user_id":"tester","message_type":"private"}'
```

### 停止/删除容器
```bash
docker stop qqbot
docker rm qqbot
```

### 重新启动
```bash
docker start qqbot
# 或重新运行: ./deploy.sh
```

---

## 镜像尺寸

- 构建时间: 2-5 分钟（取决于网络）
- 压缩后: 300-500 MB
- 解压后: 1.2-1.5 GB（Docker 本地）
- 运行内存: ~150-300 MB

---

## 常见问题

### Q: 上传太慢怎么办？
A: 可以分段上传，或使用国内云对象存储（OSS）临时中转

### Q: 镜像加载失败？
A: 检查 Docker daemon 是否运行，或用 `docker images` 查看本地镜像

### Q: 容器无法连接 NapCat？
A: 检查 `docker logs qqbot` 日志，确保 `HOST=0.0.0.0`，端口映射正确

### Q: 如何持久化数据？
A: 对话日志自动保存到 `qqbot-app/data/` 目录，重启容器不丢失

---

## 文件说明

- `build-image.ps1`: Windows 本地构建脚本（生成镜像包）
- `deploy.sh`: Ubuntu 服务器部署脚本（一键启动）
- `qqbot-image.tar.gz`: 打包好的 Docker 镜像

---

有问题？查看完整 README.md 或 GitHub Issues
