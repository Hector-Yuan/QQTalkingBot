#!/usr/bin/env pwsh
# QQBot Docker 镜像构建脚本（Windows PowerShell）
# 用法: .\build-image.ps1

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Green
Write-Host "QQBot Docker 镜像构建脚本" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# 检查 Docker
Write-Host "⏳ 检查 Docker..." -ForegroundColor Cyan
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Host "❌ 错误: 未检测到 Docker Desktop，请先安装" -ForegroundColor Red
  exit 1
}

# 构建镜像
Write-Host "⏳ 构建镜像 qqbot:latest..." -ForegroundColor Cyan
docker build -t qqbot:latest .
Write-Host "✅ 镜像构建完成" -ForegroundColor Green
Write-Host ""

# 保存为 tar
Write-Host "⏳ 保存镜像为 tar 文件..." -ForegroundColor Cyan
if (Test-Path "qqbot-image.tar") {
  Remove-Item "qqbot-image.tar" -Force
}
docker save -o qqbot-image.tar qqbot:latest
Write-Host "✅ qqbot-image.tar 已生成" -ForegroundColor Green
Write-Host ""

# 压缩
Write-Host "⏳ 压缩镜像文件..." -ForegroundColor Cyan
if (Test-Path "qqbot-image.tar.gz") {
  Remove-Item "qqbot-image.tar.gz" -Force
}

# 使用 7-Zip 或 gzip（如果已安装）
if (Get-Command gzip -ErrorAction SilentlyContinue) {
  gzip -f qqbot-image.tar
}
elseif (Get-Command 7z -ErrorAction SilentlyContinue) {
  7z a -tgzip qqbot-image.tar.gz qqbot-image.tar
  Remove-Item "qqbot-image.tar" -Force
}
else {
  Write-Host "⚠️  警告: 未找到压缩工具（gzip/7-Zip），保留原始 tar 文件" -ForegroundColor Yellow
  Write-Host "建议: 安装 7-Zip 或 Git Bash 来自动压缩镜像文件" -ForegroundColor Yellow
}

Write-Host "✅ 压缩完成" -ForegroundColor Green
Write-Host ""

# 显示文件信息
$fileInfo = Get-Item "qqbot-image.tar*" | ForEach-Object {
  "{0}: {1:N2} MB" -f $_.Name, ($_.Length / 1MB)
}

Write-Host "📦 生成文件:" -ForegroundColor Green
$fileInfo | ForEach-Object { Write-Host "   $_" }
Write-Host ""

Write-Host "📝 后续步骤:" -ForegroundColor Cyan
Write-Host "  1. 上传 qqbot-image.tar.gz 到 Ubuntu 服务器:" -ForegroundColor White
Write-Host "     scp qqbot-image.tar.gz root@116.62.130.37:/root/" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. 在服务器上执行部署脚本:" -ForegroundColor White
Write-Host "     cd /root/" -ForegroundColor Gray
Write-Host "     wget https://raw.githubusercontent.com/Hector-Yuan/QQTalkingBot/main/deploy.sh" -ForegroundColor Gray
Write-Host "     chmod +x deploy.sh" -ForegroundColor Gray
Write-Host "     ./deploy.sh" -ForegroundColor Gray
Write-Host ""

Write-Host "✨ 构建完成！" -ForegroundColor Green
