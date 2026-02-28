# NapCat 对接方案（NoneBot2 + DeepSeek）

## 1. 目标

- 将 NapCatQQ 稳定接入当前机器人服务（OneBot V11）
- 保证消息可达、回复可达、异常可定位
- 保证对话数据可持续沉淀为微调语料（JSONL）

## 2. 当前实现现状

基于现有代码：

- 机器人框架：NoneBot2 + OneBot V11 Adapter
- 对接方式：反向 WebSocket（Reverse WS）
- 当前监听地址：`127.0.0.1:8080`
- 目标 WS 路径：`/onebot/v11/ws`
- 大模型内核：DeepSeek Chat Completions
- 数据落盘：`data/chat_raw.jsonl` 与 `data/chat_finetune.jsonl`

结论：当前代码已具备对接基础，重点在于 NapCat 连接配置、鉴权一致性和运行稳定性。

## 3. 推荐对接架构

### 3.1 单机本地模式（推荐先用）

适合开发联调与小规模运行。

- NapCat 与 Bot 在同一台机器
- NapCat 通过反向 WS 连接 `ws://127.0.0.1:8080/onebot/v11/ws`
- 使用 `ONEBOT_ACCESS_TOKEN` 做基础鉴权（可选但建议开启）

优点：配置简单、排障快。

### 3.2 分离部署模式（后续扩展）

适合 24h 运行与远程主机部署。

- NapCat 所在机通过公网或内网穿透连接 Bot 服务
- 建议加一层反向代理（Nginx/Caddy）并启用 TLS
- 控制来源 IP，限制非授权连接

优点：可扩展、稳定性更好。

## 4. 实施步骤（按顺序）

### 步骤 A：环境与配置对齐

1. 在项目目录准备 `.env`（由 `.env.example` 复制）
2. 至少确认以下变量：
   - `HOST=127.0.0.1`
   - `PORT=8080`
   - `ONEBOT_ACCESS_TOKEN=你的token`（建议设置）
   - `DEEPSEEK_API_KEY=你的key`
3. 启动 Bot：`python bot.py`

### 步骤 B：NapCat 端配置

在 NapCat 的 OneBot 设置中：

- 协议版本：OneBot V11
- 连接方式：反向 WebSocket（Reverse WS）
- 地址：`ws://127.0.0.1:8080/onebot/v11/ws`
- Access Token：与 `.env` 中 `ONEBOT_ACCESS_TOKEN` 完全一致
- 心跳：建议开启（用于断线检测）

### 步骤 C：联调验证

按下面顺序验证：

1. 连接建立：Bot 日志出现连接成功相关信息
2. 指令验证：发送 `/ping`，应回复 `pong`
3. 模型验证：`@机器人 你好`，应返回 DeepSeek 内容
4. 数据验证：检查 `data/chat_raw.jsonl` 与 `data/chat_finetune.jsonl` 是否新增记录

### 步骤 D：稳定性加固

- 进程守护：使用 NSSM / PM2 / 任务计划保证异常自动拉起
- 日志分级：保留连接日志、错误日志、请求失败日志
- 限流策略：群聊高峰时考虑对同一用户设置最小请求间隔
- 失败兜底：DeepSeek 调用失败时返回固定友好提示

## 5. 验收标准

满足以下条件即视为对接完成：

- NapCat 与 Bot 在 10 分钟内无断连
- 指令和普通聊天都可稳定回复
- 断开网络后恢复网络，连接可自动恢复
- 对话日志可持续写入 JSONL，且格式可被脚本逐行解析

## 6. 常见问题与排障

### 6.1 连不上 WS

排查顺序：

1. Bot 是否已启动并监听 8080
2. NapCat WS 地址是否写成 `ws://127.0.0.1:8080/onebot/v11/ws`
3. 防火墙是否拦截本地或目标端口
4. Token 是否一致（空值也要保持两端一致）

### 6.2 能收到消息但不回复

- 检查是否 `@机器人`（当前聊天规则为 `to_me()`）
- 检查 `DEEPSEEK_API_KEY` 是否填写
- 检查 DeepSeek 返回是否报 HTTP 错误

### 6.3 日志文件没有增长

- 检查 `SAVE_DATASET_ENABLED=true`
- 检查 `DATASET_DIR` 是否有写权限
- 检查是否走到了 DeepSeek 对话分支（帮助指令不会写入）

## 7. 数据集治理建议（用于微调）

- 脱敏：清洗手机号、邮箱、身份证、QQ号等个人信息
- 过滤：剔除辱骂、无意义短句、报错回复样本
- 标注：可增加字段区分场景（私聊/群聊、业务主题）
- 版本化：按日期切分数据文件，保留清洗脚本与变更记录

## 8. 下一步建议

- 增加多轮上下文记忆（按会话窗口）
- 增加数据清洗脚本（raw -> clean_finetune）
- 增加管理指令（开关记录、查看状态、热更新系统提示词）
