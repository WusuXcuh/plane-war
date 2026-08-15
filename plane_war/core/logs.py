"""终端日志输出。

原本 game.py 和 systems.py 各自定义了一份相同的 log 函数，现在统一放在这里，
避免以后改日志格式时漏改一处。
"""

import datetime


def log(message):
    """输出带时间戳的日志到终端。"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
