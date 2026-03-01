"""项目运行配置模块。

职责：
1) 读取 `.env` 并暴露全局配置常量。
2) 提供启动前配置自检，避免关键配置缺失时静默失败。
3) 初始化数据目录，确保日志落盘路径可用。
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from nonebot.log import logger

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env", override=False)


# DeepSeek 连接与采样参数
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "").strip()
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "").strip()
DEEPSEEK_SYSTEM_PROMPT = os.getenv("DEEPSEEK_SYSTEM_PROMPT", "").strip()
DEEPSEEK_TIMEOUT = float(os.getenv("DEEPSEEK_TIMEOUT", "30")) if os.getenv("DEEPSEEK_TIMEOUT") else 30.0
QQ_MAX_REPLY_CHARS = int(os.getenv("QQ_MAX_REPLY_CHARS", "1000"))
QQ_SPLIT_LONG_REPLY = os.getenv("QQ_SPLIT_LONG_REPLY", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
DEEPSEEK_TEMPERATURE = float(os.getenv("DEEPSEEK_TEMPERATURE", "0.9")) if os.getenv("DEEPSEEK_TEMPERATURE") else 0.9
DEEPSEEK_TOP_P = float(os.getenv("DEEPSEEK_TOP_P", "0.92")) if os.getenv("DEEPSEEK_TOP_P") else 0.92
DEEPSEEK_MAX_TOKENS = int(os.getenv("DEEPSEEK_MAX_TOKENS", "350")) if os.getenv("DEEPSEEK_MAX_TOKENS") else 350

# 风格控制与回复清洗开关
STYLE_FEWSHOT_ENABLED = os.getenv("STYLE_FEWSHOT_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
STYLE_FEWSHOT_JSON = os.getenv("STYLE_FEWSHOT_JSON", "").strip()
DEFAULT_STYLE_FEWSHOT_JSON = os.getenv("DEFAULT_STYLE_FEWSHOT_JSON", "").strip()
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
CONTEXT_MAX_TURNS = int(os.getenv("CONTEXT_MAX_TURNS", "6"))
CONTEXT_SCOPE = os.getenv("CONTEXT_SCOPE", "auto").strip().lower()
CONTEXT_GROUP_SPEAKER_TAG = os.getenv("CONTEXT_GROUP_SPEAKER_TAG", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
CONTEXT_RESTORE_ON_START = (
    os.getenv("CONTEXT_RESTORE_ON_START", "true").strip().lower() in {"1", "true", "yes", "on"}
)
CONTEXT_RESTORE_MAX_MESSAGES = int(os.getenv("CONTEXT_RESTORE_MAX_MESSAGES", "40"))
CONTEXT_PERSIST_ENABLED = os.getenv("CONTEXT_PERSIST_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
CONTEXT_PERSIST_FILE = os.getenv("CONTEXT_PERSIST_FILE", "context_sessions.json").strip()

# 数据集落盘配置
SAVE_DATASET_ENABLED = os.getenv("SAVE_DATASET_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
DATASET_DIR = Path(os.getenv("DATASET_DIR", "./data").strip())
RAW_LOG_FILE = os.getenv("RAW_LOG_FILE", "chat_raw.jsonl").strip()
FINETUNE_FILE = os.getenv("FINETUNE_FILE", "chat_finetune.jsonl").strip()

# 默认 few-shot 示例，从 .env 中读取
DEFAULT_STYLE_FEWSHOT = []
if DEFAULT_STYLE_FEWSHOT_JSON:
    try:
        parsed = json.loads(DEFAULT_STYLE_FEWSHOT_JSON)
        if isinstance(parsed, list):
            DEFAULT_STYLE_FEWSHOT = parsed
    except Exception:
        pass

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
