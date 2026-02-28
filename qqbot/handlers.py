"""消息处理器注册模块。

将 NoneBot 的 matcher 定义集中在这里，便于 code review 时按“入口路由”理解系统行为。
"""

import os

import nonebot
from nonebot import on_command, on_message, on_regex
from nonebot.adapters.onebot.v11 import Message, MessageEvent
from nonebot.rule import to_me

from .config import (
    CONTEXT_ENABLED,
    CONTEXT_MAX_TURNS,
    DATASET_DIR,
    DEEPSEEK_MODEL,
    DEEPSEEK_API_KEY,
    SAVE_DATASET_ENABLED,
)
from .context_store import clear_context, get_conversation_id
from .dataset_store import save_dialog_record
from .deepseek_client import ask_deepseek
from .text_utils import split_reply_for_qq


def register_handlers() -> None:
    """注册全部命令与聊天处理器。"""

    # 基础健康检查命令
    ping = on_command("ping", priority=5, block=True)
    # 运行状态查询命令
    status = on_command("status", priority=5, block=True)
    # 当前会话上下文清理命令
    clearctx = on_command("clearctx", priority=5, block=True)
    # 正则复读命令（便于快速测试消息通道）
    repeat = on_regex(r"^复读\s+(.+)$", priority=10, block=True)
    # 主聊天入口：仅响应 @机器人 的消息
    chat = on_message(rule=to_me(), priority=20, block=False)

    @ping.handle()
    async def handle_ping() -> None:
        await ping.finish("pong")

    @status.handle()
    async def handle_status() -> None:
        """输出运行态信息，便于排查接入和配置问题。"""

        connected_bots = len(nonebot.get_bots())
        onebot_token_set = bool(os.getenv("ONEBOT_ACCESS_TOKEN", "").strip())
        deepseek_key_set = bool(DEEPSEEK_API_KEY)

        reply = (
            "运行状态：\n"
            f"- NapCat连接数: {connected_bots}\n"
            f"- OneBot Token: {'已设置' if onebot_token_set else '未设置'}\n"
            f"- DeepSeek Key: {'已设置' if deepseek_key_set else '未设置'}\n"
            f"- DeepSeek 模型: {DEEPSEEK_MODEL}\n"
            f"- 上下文记忆: {'开启' if CONTEXT_ENABLED else '关闭'} (最近{CONTEXT_MAX_TURNS}轮)\n"
            f"- 数据集记录: {'开启' if SAVE_DATASET_ENABLED else '关闭'}\n"
            f"- 数据目录: {DATASET_DIR}"
        )
        await status.finish(reply)

    @clearctx.handle()
    async def handle_clearctx(event: MessageEvent) -> None:
        """清空当前会话上下文（按 conversation_id 生效）。"""

        conversation_id = get_conversation_id(event)
        await clear_context(conversation_id)
        await clearctx.finish("当前会话上下文已清空。")

    @repeat.handle()
    async def handle_repeat(event: MessageEvent) -> None:
        """复读测试：`复读 xxx` -> `xxx`。"""

        text = str(event.get_message()).strip()
        content = text.split(maxsplit=1)[1] if " " in text else ""
        await repeat.finish(Message(content or "你要我复读什么？"))

    @chat.handle()
    async def handle_chat(event: MessageEvent) -> None:
        """主聊天流程。

        - 处理帮助词。
        - 调用 DeepSeek 生成回复。
        - 记录数据集样本（失败不影响主流程）。
        - 按 QQ 限长自动分片发送。
        """

        text = str(event.get_message()).strip()
        if not text:
            return

        if text in {"帮助", "help", "/help"}:
            reply = "可用指令：/ping、/status、/clearctx、复读 xxx；或 @我 后直接提问（由 DeepSeek 回复）。"
        else:
            reply = await ask_deepseek(event, text)
            try:
                await save_dialog_record(event, text, reply)
            except Exception:
                pass

        chunks = split_reply_for_qq(reply)
        for chunk in chunks[:-1]:
            await chat.send(chunk)
        await chat.finish(chunks[-1])
