"""本地存档读写。

目前只管理无尽模式最高分，后续如果有设置或玩家档案也可以放到这里。
"""

import os
import re


class HighScoreStore:
    def __init__(self, base_dir, log_func):
        self.user_data_dir = os.path.join(base_dir, "user_data")
        self.readme_file = os.path.join(self.user_data_dir, "README.md")
        self.old_high_score_file = os.path.join(self.user_data_dir, "high_score.txt")
        self.log = log_func

    def load(self):
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            readme_score = 0
            if os.path.exists(self.readme_file):
                with open(self.readme_file, "r", encoding="utf-8") as f:
                    match = re.search(r"无尽模式最高记录:\s*(\d+)", f.read())
                    if match:
                        readme_score = max(0, int(match.group(1)))

            return max(readme_score, self._load_old_high_score())
        except (OSError, ValueError) as exc:
            self.log(f"读取最高分失败: {exc}")
            return 0

    def save(self, score):
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            content = self._read_readme()
            line = f"无尽模式最高记录: {int(score)}"
            if re.search(r"无尽模式最高记录:\s*\d+", content):
                content = re.sub(r"无尽模式最高记录:\s*\d+", line, content)
            else:
                content = content.rstrip() + "\n\n" + line + "\n"

            with open(self.readme_file, "w", encoding="utf-8") as f:
                f.write(content)
        except OSError as exc:
            self.log(f"保存最高分失败: {exc}")

    def _load_old_high_score(self):
        if not os.path.exists(self.old_high_score_file):
            return 0

        with open(self.old_high_score_file, "r", encoding="utf-8") as f:
            return max(0, int(f.read().strip() or 0))

    def _read_readme(self):
        if os.path.exists(self.readme_file):
            with open(self.readme_file, "r", encoding="utf-8") as f:
                return f.read()
        return "# 用户数据\n\n这里保存游戏的用户数据。\n"
