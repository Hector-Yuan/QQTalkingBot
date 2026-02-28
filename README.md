# 简易 QQ 聊天 Bot（NapCatQQ + DeepSeek）

这是一个基于 `NoneBot2 + OneBot V11` 的最小聊天机器人示例，可与 NapCatQQ 对接，并将聊天内核接到 DeepSeek API。

## 1. 安装依赖

在项目根目录执行：

```powershell
pip install -r requirements.txt
```

## 2. 配置环境变量

复制模板：

```powershell
Copy-Item .env.example .env
```

如果你在 NapCatQQ 里设置了 token，请将 `.env` 的 `ONEBOT_ACCESS_TOKEN` 改成同样值。

同时请在 `.env` 中填写：

- `DEEPSEEK_API_KEY`：你的 DeepSeek API Key（必填）
- `DEEPSEEK_MODEL`：默认 `deepseek-chat`
- `DEEPSEEK_BASE_URL`：默认 `https://api.deepseek.com`
- `QQ_MAX_REPLY_CHARS`：单条回复最大字符数，默认 `4000`（超出会自动截断）
- `QQ_SPLIT_LONG_REPLY`：超长时自动拆成多条消息发送（默认 `true`）
- `DEEPSEEK_TEMPERATURE`：回复发散度，默认 `0.9`（更自然）
- `DEEPSEEK_TOP_P`：采样范围，默认 `0.92`
- `DEEPSEEK_MAX_TOKENS`：单次回复长度上限，默认 `350`
- `STYLE_FEWSHOT_ENABLED`：是否启用风格示例注入（默认 `true`）
- `STYLE_FEWSHOT_JSON`：可选，自定义风格示例 JSON 数组
- `CONTEXT_ENABLED`：是否启用多轮上下文（默认 `true`）
- `CONTEXT_MAX_TURNS`：每个会话保留最近几轮（默认 `6`）
- `CONTEXT_SCOPE`：上下文范围，`auto`/`group`/`user`（默认 `auto`）
- `CONTEXT_GROUP_SPEAKER_TAG`：群聊共享上下文时，是否给每条用户消息打上发言人标识（默认 `true`，建议开启）
- `CONTEXT_RESTORE_ON_START`：重启后从日志恢复上下文（默认 `true`）
- `CONTEXT_RESTORE_MAX_MESSAGES`：每会话最大恢复消息条数（默认 `40`）
- `CONTEXT_PERSIST_ENABLED`：是否启用会话快照持久化（默认 `true`）
- `CONTEXT_PERSIST_FILE`：会话快照文件名（默认 `context_sessions.json`）
- `SAVE_DATASET_ENABLED`：是否保存对话数据（默认 `true`）
- `DATASET_DIR`：数据目录（默认 `./data`）
- `FINETUNE_FILE`：微调数据文件名（默认 `chat_finetune.jsonl`）

## 3. 启动 Bot

```powershell
python bot.py
```

默认监听：`127.0.0.1:8080`

## 4. 在 NapCatQQ 里配置反向 WebSocket（推荐）

在 NapCatQQ 的 OneBot 配置中：

- 协议：OneBot V11
- 连接方式：反向 WebSocket（Reverse WS）
- WS 地址：`ws://127.0.0.1:8080/onebot/v11/ws`
- Access Token：与 `.env` 的 `ONEBOT_ACCESS_TOKEN` 保持一致（可为空）

保存并重连后，看到连接成功日志即可。

## 5. 试用

- 发送 `/ping`，应回复 `pong`
- 发送 `/status`，可查看对接与配置状态
- 发送 `/clearctx`，可清空当前会话上下文
- 发送 `复读 今天天气不错`，应复读后半句
- 在群聊中 `@机器人 帮助`，应返回帮助文本
- 在群聊中 `@机器人 你好`，应由 DeepSeek 生成回复

### 多轮上下文说明

- 机器人会按会话（私聊或群聊）缓存最近 `CONTEXT_MAX_TURNS` 轮对话。
- 每次调用 DeepSeek 时，会附带这些历史消息，让回复更连贯。
- 当你希望“重开话题”时，发送 `/clearctx` 即可清空当前会话记忆。
- 建议保持 `CONTEXT_SCOPE=auto`：群聊走群上下文、私聊走用户上下文。
- 若群里多人都在和 bot 说话，建议保持 `CONTEXT_GROUP_SPEAKER_TAG=true`，可减少“把不同人当同一人”的串台。
- 若经常重启 bot，保持 `CONTEXT_RESTORE_ON_START=true`，可减少“重启后断上下文”。
- 若希望重启后更稳定续聊，保持 `CONTEXT_PERSIST_ENABLED=true`，程序会将会话写入 `DATASET_DIR/context_sessions.json`。

### 让回复更像真人

- 默认系统提示词已改为“朋友式口语聊天”风格。
- 默认会注入少量风格示例（few-shot），让语气更稳定。
- 如果你想定制说话风格，可在 `.env` 中设置 `STYLE_FEWSHOT_JSON`，例如：

```json
[{"user":"我今天好累","assistant":"辛苦了，先歇一会儿，我陪你慢慢缓过来。"}]
```

## 6. 对话数据存储（用于微调）

当 `SAVE_DATASET_ENABLED=true` 时，每次由 DeepSeek 生成的回复都会写入：

- `DATASET_DIR/chat_raw.jsonl`：原始对话日志（含用户、群、时间等元信息）
- `DATASET_DIR/chat_finetune.jsonl`：微调友好的 `messages` 结构

`chat_finetune.jsonl` 每行类似：

```json
{"messages":[{"role":"system","content":"..."},{"role":"user","content":"你好"},{"role":"assistant","content":"你好呀"}],"metadata":{"conversation_id":"group:123:456"}}
```

你可以后续基于这个文件做清洗（脱敏、过滤低质量样本）再用于模型微调。

## 文件说明

- `bot.py`：程序入口（仅负责启动）
- `qqbot/app.py`：NoneBot 初始化与启动
- `qqbot/handlers.py`：指令与消息处理
- `qqbot/deepseek_client.py`：DeepSeek 调用与回复生成
- `qqbot/context_store.py`：上下文会话管理与恢复
- `qqbot/dataset_store.py`：对话日志与微调数据落盘
- `qqbot/config.py`：环境变量与运行配置
- `qqbot/text_utils.py`：文本清洗与QQ消息分片
- `requirements.txt`：依赖
- `.env.example`：环境变量模板

## 7. Docker Compose（仅 Bot）

1. 在 `.env` 中至少配置：
	- `PORT`（例如 `8082`）
	- `ONEBOT_ACCESS_TOKEN`
	- `DEEPSEEK_API_KEY`
2. 启动：

```powershell
docker compose up -d --build
```

3. 如果 NapCat 运行在同一台服务器（原生安装），在 OneBot 里配置反向 WS：
	- `ws://127.0.0.1:${PORT}/onebot/v11/ws`
	- Access Token 与 `.env` 的 `ONEBOT_ACCESS_TOKEN` 一致
