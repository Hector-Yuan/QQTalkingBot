"""本地联调测试接口。

用于在不上线 NapCat 的情况下，直接通过 HTTP 调用和机器人同一套生成逻辑，
便于调 prompt、采样参数和上下文策略。
"""

from fastapi import Header, HTTPException
from pydantic import BaseModel, Field
import nonebot

from .config import TEST_API_ENABLED, TEST_API_TOKEN
from .context_store import build_conversation_id
from .deepseek_client import ask_deepseek_for_session


class DevChatRequest(BaseModel):
    text: str = Field(..., min_length=1, description="用户输入")
    message_type: str = Field(default="private", description="private/group")
    user_id: str = Field(default="dev-user", description="测试用户ID")
    group_id: str | None = Field(default=None, description="测试群ID")
    conversation_id: str | None = Field(default=None, description="可选：手动指定会话键")


def register_test_api() -> None:
    """注册测试接口。"""

    if not TEST_API_ENABLED:
        return

    app = nonebot.get_app()

    @app.post("/dev/chat")
    async def dev_chat(payload: DevChatRequest, x_test_token: str | None = Header(default=None)) -> dict:
        if TEST_API_TOKEN and x_test_token != TEST_API_TOKEN:
            raise HTTPException(status_code=401, detail="invalid test token")

        conversation_id = payload.conversation_id or build_conversation_id(
            message_type=payload.message_type,
            user_id=payload.user_id,
            group_id=payload.group_id,
        )

        reply = await ask_deepseek_for_session(
            user_text=payload.text,
            message_type=payload.message_type,
            user_id=payload.user_id,
            group_id=payload.group_id,
            conversation_id=conversation_id,
        )

        return {
            "ok": True,
            "conversation_id": conversation_id,
            "reply": reply,
        }
