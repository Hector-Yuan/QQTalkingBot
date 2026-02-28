"""数据集落盘模块。

将对话同时写入：
- `chat_raw.jsonl`：保留事件元信息，便于回放/排障。
- `chat_finetune.jsonl`：微调友好的 messages 结构。
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from nonebot.adapters.onebot.v11 import MessageEvent

from .config import DATASET_DIR, DEEPSEEK_MODEL, DEEPSEEK_SYSTEM_PROMPT, FINETUNE_FILE, RAW_LOG_FILE, SAVE_DATASET_ENABLED
from .context_store import get_conversation_id

WRITE_LOCK = asyncio.Lock()


def _append_jsonl(path: Path, payload: dict) -> None:
    """以 JSONL 形式追加单条记录。"""

    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


async def save_dialog_record(
    event: MessageEvent,
    user_text: str,
    assistant_text: str,
) -> None:
    """保存一轮问答到数据文件。

    并发写入使用 `WRITE_LOCK` 保护，避免多协程同时写造成行级交错。
    """

    if not SAVE_DATASET_ENABLED:
        return

    timestamp = datetime.now().isoformat(timespec="seconds")
    event_time = datetime.fromtimestamp(event.time).isoformat(timespec="seconds")
    group_id = getattr(event, "group_id", None)
    conversation_id = get_conversation_id(event)

    raw_payload = {
        "timestamp": timestamp,
        "event_time": event_time,
        "platform": "qq",
        "adapter": "onebot.v11",
        "model": DEEPSEEK_MODEL,
        "message_id": event.message_id,
        "conversation_id": conversation_id,
        "message_type": event.message_type,
        "user_id": event.user_id,
        "group_id": group_id,
        "user_text": user_text,
        "assistant_text": assistant_text,
    }

    finetune_payload = {
        "messages": [
            {"role": "system", "content": DEEPSEEK_SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text},
        ],
        "metadata": {
            "timestamp": timestamp,
            "conversation_id": conversation_id,
            "message_type": event.message_type,
            "user_id": event.user_id,
            "group_id": group_id,
            "source": "napcatqq",
            "model": DEEPSEEK_MODEL,
        },
    }

    async with WRITE_LOCK:
        _append_jsonl(DATASET_DIR / RAW_LOG_FILE, raw_payload)
        _append_jsonl(DATASET_DIR / FINETUNE_FILE, finetune_payload)
