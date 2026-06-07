"""本地存档读写。

目前只管理无尽模式最高分，后续如果有设置或玩家档案也可以放到这里。
"""

import os


class HighScoreStore:
    def __init__(self, base_dir, log_func):
        self.user_data_dir = os.path.join(base_dir, "user_data")
        self.high_score_file = os.path.join(self.user_data_dir, "high_score.txt")
        self.log = log_func

    def load(self):
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            if not os.path.exists(self.high_score_file):
                return 0

            with open(self.high_score_file, "r", encoding="utf-8") as f:
                return max(0, int(f.read().strip() or 0))
        except (OSError, ValueError) as exc:
            self.log(f"读取最高分失败: {exc}")
            return 0

    def save(self, score):
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            with open(self.high_score_file, "w", encoding="utf-8") as f:
                f.write(str(score))
        except OSError as exc:
            self.log(f"保存最高分失败: {exc}")
