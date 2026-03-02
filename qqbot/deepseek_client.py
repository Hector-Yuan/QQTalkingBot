"""DeepSeek 调用模块。

主流程：
1) 构建 system/few-shot/history/user 消息。
2) 发起 chat/completions 请求。
3) 清洗回复文本、做长度保护。
4) 将本轮写回会话上下文。
"""

import json
import asyncio

import httpx
from nonebot.adapters.onebot.v11 import MessageEvent

from .config import (
    CONTEXT_ENABLED,
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MAX_TOKENS,
    DEEPSEEK_MODEL,
    DEEPSEEK_SYSTEM_PROMPT,
    DEEPSEEK_TEMPERATURE,
    DEEPSEEK_TIMEOUT,
    DEEPSEEK_TOP_P,
    DEFAULT_STYLE_FEWSHOT,
    PLAIN_REPLY_ONLY,
    STYLE_FEWSHOT_ENABLED,
    STYLE_FEWSHOT_JSON,
)
from .context_store import append_turn, build_context_user_text, get_conversation_id, get_history
from .context_store import build_conversation_id
from .text_utils import enforce_reply_length_limit, sanitize_reply_text


_CONVERSATION_LOCKS: dict[str, asyncio.Lock] = {}


def _get_conversation_lock(conversation_id: str) -> asyncio.Lock:
    lock = _CONVERSATION_LOCKS.get(conversation_id)
    if lock is None:
        lock = asyncio.Lock()
        _CONVERSATION_LOCKS[conversation_id] = lock
    return lock


def build_style_fewshot_messages() -> list[dict]:
    """生成 few-shot 消息对。

    当 `STYLE_FEWSHOT_JSON` 可解析且为数组时，优先使用自定义示例；
    否则回退到默认示例。
    """

    examples = DEFAULT_STYLE_FEWSHOT
    if STYLE_FEWSHOT_JSON:
        try:
            parsed = json.loads(STYLE_FEWSHOT_JSON)
            if isinstance(parsed, list):
                examples = parsed
        except Exception:
            pass

    messages = []
    for item in examples:
        user_text = str(item.get("user", "")).strip() if isinstance(item, dict) else ""
        assistant_text = (
            str(item.get("assistant", "")).strip() if isinstance(item, dict) else ""
        )
        if user_text and assistant_text:
            messages.append({"role": "user", "content": user_text})
            messages.append({"role": "assistant", "content": assistant_text})
    return messages


async def ask_deepseek(event: MessageEvent, user_text: str) -> str:
    """调用 DeepSeek 获取回复。

    参数：
    - event: OneBot 消息事件，提供用户/群上下文。
    - user_text: 用户原始输入文本。

    返回：
    - 面向 QQ 发送的纯文本回复（已做异常兜底与长度控制）。
    """

    if not DEEPSEEK_API_KEY:
        return "未配置 DEEPSEEK_API_KEY，请先在 .env 中填写。"

    group_id = getattr(event, "group_id", None)
    return await ask_deepseek_for_session(
        user_text=user_text,
        message_type=event.message_type,
        user_id=event.user_id,
        group_id=group_id,
        conversation_id=get_conversation_id(event),
    )


async def ask_deepseek_for_session(
    user_text: str,
    message_type: str = "private",
    user_id: str | int = "dev",
    group_id: str | int | None = None,
    conversation_id: str | None = None,
) -> str:
    """按会话参数调用 DeepSeek（用于 HTTP 测试与非 OneBot 场景）。

    当 `conversation_id` 未提供时，会按当前上下文策略自动生成会话键。
    """

    resolved_conversation_id = conversation_id or build_conversation_id(message_type, user_id, group_id)
    lock = _get_conversation_lock(resolved_conversation_id)

    async with lock:
        context_user_text = build_context_user_text(
            message_type=message_type,
            user_id=user_id,
            group_id=group_id,
            user_text=user_text,
        )
        if not context_user_text:
            return "你先说点内容，我再接。"

        history = await get_history(resolved_conversation_id)

        endpoint = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }
        messages = [{"role": "system", "content": DEEPSEEK_SYSTEM_PROMPT}]
        if STYLE_FEWSHOT_ENABLED:
            messages.extend(build_style_fewshot_messages())
        if CONTEXT_ENABLED and history:
            messages.extend(history)
        messages.append({"role": "user", "content": context_user_text})

        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": messages,
            "temperature": DEEPSEEK_TEMPERATURE,
            "top_p": DEEPSEEK_TOP_P,
            "max_tokens": DEEPSEEK_MAX_TOKENS,
        }

        try:
            async with httpx.AsyncClient(timeout=DEEPSEEK_TIMEOUT) as client:
                response = await client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as error:
            return f"DeepSeek 接口返回错误：HTTP {error.response.status_code}"
        except Exception:
            return "调用 DeepSeek 失败，请检查网络或 API 配置。"

        choices = data.get("choices") or []
        if not choices:
            return "DeepSeek 返回为空，请稍后重试。"

        content = (choices[0].get("message") or {}).get("content", "")
        text = str(content).strip()
        if not text:
            return "DeepSeek 未返回有效文本。"

        if PLAIN_REPLY_ONLY:
            text = sanitize_reply_text(text)
            if not text:
                text = "我换个更直白的说法：你可以再说具体一点，我好给你更贴近的建议。"

        text = enforce_reply_length_limit(text)

        if CONTEXT_ENABLED:
            await append_turn(resolved_conversation_id, context_user_text, text)

        return text
