"""会话上下文存储模块。

本模块维护机器人多轮对话记忆，支持：
- 不同会话键（群/私聊/用户）路由。
- 内存缓存 + 快照持久化。
- 启动时从快照或历史日志恢复上下文。

并发说明：
- `SESSION_HISTORY` 是进程内共享状态。
- 所有读写通过 `HISTORY_LOCK` 串行化，避免并发事件下出现竞态。
"""

import asyncio
import json
from collections import defaultdict

from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.log import logger

from .config import (
    CONTEXT_ENABLED,
    CONTEXT_GROUP_SPEAKER_TAG,
    CONTEXT_MAX_TURNS,
    CONTEXT_PERSIST_ENABLED,
    CONTEXT_PERSIST_FILE,
    CONTEXT_RESTORE_MAX_MESSAGES,
    CONTEXT_RESTORE_ON_START,
    CONTEXT_SCOPE,
    DATASET_DIR,
    RAW_LOG_FILE,
)

HISTORY_LOCK = asyncio.Lock()
SESSION_HISTORY: dict[str, list[dict]] = defaultdict(list)


def build_conversation_id(message_type: str, user_id: str | int, group_id: str | int | None) -> str:
    """构建会话键。

    规则由 `CONTEXT_SCOPE` 决定：
    - group: 强制按群聚合。
    - user: 强制按用户聚合。
    - auto : 群聊按群，私聊按用户。
    """

    if CONTEXT_SCOPE == "group" and group_id:
        return f"group:{group_id}"
    if CONTEXT_SCOPE == "user":
        return f"user:{user_id}"

    if group_id:
        return f"group:{group_id}"
    if str(message_type) == "private":
        return f"private:{user_id}"
    return f"user:{user_id}"


def get_conversation_id(event: MessageEvent) -> str:
    """从 OneBot 事件提取会话键。"""

    group_id = getattr(event, "group_id", None)
    return build_conversation_id(event.message_type, event.user_id, group_id)


def build_context_user_text(
    message_type: str,
    user_id: str | int,
    group_id: str | int | None,
    user_text: str,
) -> str:
    """构建写入模型上下文的用户文本。

    在群共享上下文模式下，给用户发言增加 `[用户ID]` 前缀，
    用于降低“不同人被当同一人”的串台风险。
    """

    text = str(user_text or "").strip()
    if not text:
        return ""

    if CONTEXT_GROUP_SPEAKER_TAG and (CONTEXT_SCOPE == "group" or (CONTEXT_SCOPE == "auto" and group_id)):
        return f"[用户{user_id}] {text}"
    return text


def persist_session_history_unlocked() -> None:
    """将内存上下文快照写盘。

    注意：本函数不自行加锁，调用方需保证已在 `HISTORY_LOCK` 保护范围内。
    """

    if not CONTEXT_PERSIST_ENABLED:
        return

    snapshot_path = DATASET_DIR / CONTEXT_PERSIST_FILE
    payload = {
        "version": 1,
        "scope": CONTEXT_SCOPE,
        "sessions": dict(SESSION_HISTORY),
    }
    snapshot_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _load_session_snapshot() -> bool:
    """从快照文件恢复上下文。

    返回值：
    - True: 成功恢复至少一个会话。
    - False: 无可用快照或格式无效。
    """

    if not CONTEXT_PERSIST_ENABLED:
        return False

    snapshot_path = DATASET_DIR / CONTEXT_PERSIST_FILE
    if not snapshot_path.exists():
        return False

    try:
        raw = snapshot_path.read_text(encoding="utf-8").strip()
        if not raw:
            return False
        data = json.loads(raw)
        sessions = data.get("sessions") if isinstance(data, dict) else None
        if not isinstance(sessions, dict):
            return False

        loaded = 0
        for conversation_id, messages in sessions.items():
            if not isinstance(messages, list):
                continue

            valid_messages = []
            for message in messages:
                if isinstance(message, dict):
                    role = str(message.get("role", "")).strip()
                    content = str(message.get("content", "")).strip()
                    if role in {"user", "assistant"} and content:
                        valid_messages.append({"role": role, "content": content})

            if valid_messages:
                max_messages = CONTEXT_MAX_TURNS * 2
                SESSION_HISTORY[str(conversation_id)] = valid_messages[-max_messages:]
                loaded += 1

        if loaded:
            logger.info("已从会话快照恢复上下文：{} 个会话", loaded)
            return True
    except Exception:
        logger.warning("会话快照读取失败，将尝试从日志恢复。")

    return False


def restore_session_history() -> None:
    """启动时恢复上下文。

    恢复顺序：
    1) 优先快照文件（结构稳定、读取快）。
    2) 回退到 `chat_raw.jsonl` 逐行回放。
    """

    if not (CONTEXT_ENABLED and CONTEXT_RESTORE_ON_START):
        return

    if _load_session_snapshot():
        return

    raw_path = DATASET_DIR / RAW_LOG_FILE
    if not raw_path.exists():
        return

    restored = 0
    try:
        with raw_path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except Exception:
                    continue
                message_type = str(record.get("message_type", "")).strip() or "private"
                user_id = str(record.get("user_id", "")).strip()
                group_id = record.get("group_id")
                user_text = str(record.get("user_text", "")).strip()
                assistant_text = str(record.get("assistant_text", "")).strip()
                if not user_id or not user_text or not assistant_text:
                    continue

                conversation_id = build_conversation_id(message_type, user_id, group_id)
                context_user_text = build_context_user_text(
                    message_type=message_type,
                    user_id=user_id,
                    group_id=group_id,
                    user_text=user_text,
                )
                if not context_user_text:
                    continue

                session_messages = SESSION_HISTORY[conversation_id]
                session_messages.append({"role": "user", "content": context_user_text})
                session_messages.append({"role": "assistant", "content": assistant_text})
                if len(session_messages) > CONTEXT_RESTORE_MAX_MESSAGES:
                    SESSION_HISTORY[conversation_id] = session_messages[-CONTEXT_RESTORE_MAX_MESSAGES:]
                restored += 1

        if restored:
            logger.info("已从日志恢复上下文：{} 条记录，{} 个会话", restored, len(SESSION_HISTORY))
            persist_session_history_unlocked()
    except Exception:
        logger.warning("上下文恢复失败，将继续使用空内存上下文。")


async def clear_context(conversation_id: str) -> None:
    """清空指定会话的上下文并持久化。"""

    async with HISTORY_LOCK:
        SESSION_HISTORY.pop(conversation_id, None)
        persist_session_history_unlocked()


async def get_history(conversation_id: str) -> list[dict]:
    """读取指定会话历史（返回副本，避免外部误改内存状态）。"""

    async with HISTORY_LOCK:
        return list(SESSION_HISTORY.get(conversation_id, []))


async def append_turn(conversation_id: str, user_text: str, assistant_text: str) -> None:
    """追加一轮对话并裁剪到窗口大小。

    窗口长度 = `CONTEXT_MAX_TURNS * 2`（user + assistant）。
    """

    async with HISTORY_LOCK:
        session_messages = SESSION_HISTORY[conversation_id]
        session_messages.append({"role": "user", "content": user_text})
        session_messages.append({"role": "assistant", "content": assistant_text})
        max_messages = CONTEXT_MAX_TURNS * 2
        if len(session_messages) > max_messages:
            SESSION_HISTORY[conversation_id] = session_messages[-max_messages:]
        persist_session_history_unlocked()
