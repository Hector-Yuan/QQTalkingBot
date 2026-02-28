"""文本后处理工具模块。

用于把模型输出转换成更适合 QQ 发送的纯文本：
- 清洗 markdown/列表痕迹。
- 限制单条长度。
- 需要时自动分片发送。
"""

import re

from .config import QQ_MAX_REPLY_CHARS, QQ_SPLIT_LONG_REPLY


def sanitize_reply_text(text: str) -> str:
    """清洗非聊天体格式。

    目标：尽量保留语义，去掉标题、列表、舞台括号等格式噪音。
    """

    cleaned = str(text or "").replace("\r\n", "\n").replace("\r", "\n")

    cleaned = re.sub(r"^\s*[（(][^（）()\n]{1,24}[）)]\s*", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*[（(][^（）()\n]{1,24}[）)]\s*$", "", cleaned)
    cleaned = re.sub(
        r"(?m)^\s*(\d+[\.、\)]|[一二三四五六七八九十]+[、\.])\s*[^\n：:]{1,16}\s*$",
        "",
        cleaned,
    )

    cleaned = re.sub(r"^\s{0,3}#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*([\-\*•·◆◇■□●○▶▷➤➥※]+|\d+[\.)])\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.replace("**", "").replace("__", "").replace("`", "")
    cleaned = re.sub(r"[◆◇■□●○▶▷➤➥※]+", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
    if len(lines) >= 4:
        cleaned = " ".join(lines)

    return cleaned.strip()


def enforce_reply_length_limit(text: str) -> str:
    """硬限制单条消息长度，超出时截断并加后缀。"""

    normalized = str(text or "").strip()
    if len(normalized) <= QQ_MAX_REPLY_CHARS:
        return normalized

    suffix = "…（后略）"
    keep = max(0, QQ_MAX_REPLY_CHARS - len(suffix))
    return normalized[:keep].rstrip() + suffix


def split_reply_for_qq(text: str) -> list[str]:
    """按句读与换行拆分长回复。

    行为：
    - 短文本原样返回。
    - 超长且开启拆分时，优先按标点拆。
    - 无法按标点拆时退化为定长切片。
    """

    normalized = str(text or "").strip()
    if not normalized:
        return [""]

    if len(normalized) <= QQ_MAX_REPLY_CHARS:
        return [normalized]

    if not QQ_SPLIT_LONG_REPLY:
        return [enforce_reply_length_limit(normalized)]

    parts = re.split(r"([。！？!?；;\n])", normalized)
    segments = []
    current = ""

    for part in parts:
        if not part:
            continue

        candidate = current + part
        if len(candidate) <= QQ_MAX_REPLY_CHARS:
            current = candidate
            continue

        if current.strip():
            segments.append(current.strip())
            current = part
            continue

        start = 0
        while start < len(part):
            end = start + QQ_MAX_REPLY_CHARS
            segments.append(part[start:end].strip())
            start = end
        current = ""

    if current.strip():
        segments.append(current.strip())

    cleaned_segments = [segment for segment in segments if segment]
    return cleaned_segments or [enforce_reply_length_limit(normalized)]
