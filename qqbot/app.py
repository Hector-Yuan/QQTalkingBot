"""应用启动编排模块。"""

import nonebot
from nonebot.adapters.onebot.v11 import Adapter

from .config import validate_runtime_config
from .context_store import restore_session_history
from .handlers import register_handlers
from .test_api import register_test_api


def main() -> None:
    """启动机器人。

    顺序要求：
    1) 初始化 nonebot 与适配器。
    2) 配置自检与上下文恢复。
    3) 注册消息处理器。
    4) 进入事件循环。
    """

    nonebot.init()
    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)

    validate_runtime_config()
    restore_session_history()
    register_handlers()
    register_test_api()

    nonebot.run()
