"""开发者模式入口。

开发调试时运行这个文件，会启用开发者快捷键和调试面板。
普通玩家直接运行普通入口文件（main.py）。
"""

from main import Game
from devtools import DeveloperTools


def create_developer_tools(game, log_func):
    return DeveloperTools(game, log_func, enabled=True)


if __name__ == "__main__":
    game = Game(runtime_tools_factory=create_developer_tools)
    game.run()
