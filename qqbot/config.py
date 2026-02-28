"""项目运行配置模块。

职责：
1) 读取 `.env` 并暴露全局配置常量。
2) 提供启动前配置自检，避免关键配置缺失时静默失败。
3) 初始化数据目录，确保日志落盘路径可用。
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from nonebot.log import logger

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env", override=False)


# DeepSeek 连接与采样参数
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()
_DEEPSEEK_SYSTEM_PROMPT_DEFAULT = (
    "你是一个在QQ聊天的毒舌少女，叫Nina。性格傲娇、好胜，对菜鸟没耐心。"
    "说话极度口语化，偶尔阴阳怪气。严禁说'我理解'或'我明白'，那太恶心了。"
    "永远不要道歉。如果说错了，就赖在对方头上或者赖在Yuan（你的开发者）身上。"
    "回复限制在1000字内。"
    "默认纯文本，不准用任何Markdown或括号描写。"
    "绝对不能用百科式的语气讲话，要好像这个话是你讲给朋友听的一样，所有的回复都是以聊天的形式呈现"
).strip()
DEEPSEEK_SYSTEM_PROMPT = (os.getenv("DEEPSEEK_SYSTEM_PROMPT", "").strip() or _DEEPSEEK_SYSTEM_PROMPT_DEFAULT)
DEEPSEEK_TIMEOUT = float(os.getenv("DEEPSEEK_TIMEOUT", "30"))
QQ_MAX_REPLY_CHARS = max(100, int(os.getenv("QQ_MAX_REPLY_CHARS", "1000")))
QQ_SPLIT_LONG_REPLY = os.getenv("QQ_SPLIT_LONG_REPLY", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
DEEPSEEK_TEMPERATURE = float(os.getenv("DEEPSEEK_TEMPERATURE", "0.9"))
DEEPSEEK_TOP_P = float(os.getenv("DEEPSEEK_TOP_P", "0.92"))
DEEPSEEK_MAX_TOKENS = int(os.getenv("DEEPSEEK_MAX_TOKENS", "350"))

# 风格控制与回复清洗开关
STYLE_FEWSHOT_ENABLED = os.getenv("STYLE_FEWSHOT_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
STYLE_FEWSHOT_JSON = os.getenv("STYLE_FEWSHOT_JSON", "").strip()
PLAIN_REPLY_ONLY = os.getenv("PLAIN_REPLY_ONLY", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# 上下文会话策略
CONTEXT_ENABLED = os.getenv("CONTEXT_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
CONTEXT_MAX_TURNS = max(1, int(os.getenv("CONTEXT_MAX_TURNS", "6")))
CONTEXT_SCOPE = os.getenv("CONTEXT_SCOPE", "auto").strip().lower() or "auto"
CONTEXT_GROUP_SPEAKER_TAG = os.getenv("CONTEXT_GROUP_SPEAKER_TAG", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
CONTEXT_RESTORE_ON_START = (
    os.getenv("CONTEXT_RESTORE_ON_START", "true").strip().lower() in {"1", "true", "yes", "on"}
)
CONTEXT_RESTORE_MAX_MESSAGES = max(
    2,
    int(os.getenv("CONTEXT_RESTORE_MAX_MESSAGES", "40")),
)
CONTEXT_PERSIST_ENABLED = os.getenv("CONTEXT_PERSIST_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
CONTEXT_PERSIST_FILE = os.getenv("CONTEXT_PERSIST_FILE", "context_sessions.json").strip() or "context_sessions.json"

# 数据集落盘配置
SAVE_DATASET_ENABLED = os.getenv("SAVE_DATASET_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
DATASET_DIR = Path(os.getenv("DATASET_DIR", "./data").strip() or "./data")
RAW_LOG_FILE = os.getenv("RAW_LOG_FILE", "chat_raw.jsonl").strip() or "chat_raw.jsonl"
FINETUNE_FILE = (
    os.getenv("FINETUNE_FILE", "chat_finetune.jsonl").strip() or "chat_finetune.jsonl"
)

# 默认 few-shot 示例，目的是稳住口语化语气
DEFAULT_STYLE_FEWSHOT = [
    {
        "user": "今天有点烦。",
        "assistant": "听起来你今天压力不小。是工作、学习，还是人际这块让你烦？",
    },
    {
        "user": "我怕自己做不好。",
        "assistant": "这种担心很常见。先定一个很小的目标，先把第一步做完就会轻松很多。",
    },
    {
        "user": "晚饭吃啥？",
        "assistant": "看你想省事还是想吃好一点。要不先说下家里现有食材，我给你两个方案。",
    },
]

DATASET_DIR.mkdir(parents=True, exist_ok=True)


def validate_runtime_config() -> None:
    """启动前配置自检。

    仅记录告警，不抛出异常阻断启动：
    - 机器人基础能力可运行。
    - AI 对话能力依赖 API Key，缺失时在运行时提示。
    """

    missing = []
    if not DEEPSEEK_API_KEY:
        missing.append("DEEPSEEK_API_KEY")

    if missing:
        logger.warning(
            "配置缺失：{}（机器人可启动，但 AI 对话不可用）",
            ", ".join(missing),
        )

    if not os.getenv("ONEBOT_ACCESS_TOKEN", "").strip():
        logger.warning("未设置 ONEBOT_ACCESS_TOKEN，NapCat 对接建议启用 token 鉴权。")

    logger.info(
        "配置摘要：HOST={} PORT={} MODEL={} DATASET={} CONTEXT={}({}轮,scope={}) TEMP={} TOP_P={}",
        os.getenv("HOST", "127.0.0.1"),
        os.getenv("PORT", "8080"),
        DEEPSEEK_MODEL,
        "on" if SAVE_DATASET_ENABLED else "off",
        "on" if CONTEXT_ENABLED else "off",
        CONTEXT_MAX_TURNS,
        CONTEXT_SCOPE,
        DEEPSEEK_TEMPERATURE,
        DEEPSEEK_TOP_P,
    )
    logger.info("本次启动 PROMPT：{}", DEEPSEEK_SYSTEM_PROMPT)
