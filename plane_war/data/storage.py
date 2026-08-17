"""本地存档读写。

目前只管理无尽模式最高分。最高分保存在 user_data/high_score.json 中，
旧版本的 README.md 和 high_score.txt 仍会作为兼容兜底读取，但新的保存只会写入 JSON。
"""

import json
import os
import re

from plane_war.paths import USER_DATA_DIR


class HighScoreStore:
    """无尽模式最高分存储器。

    这个类只关心“从哪里读”和“写成什么格式”，主流程不用知道存档文件结构。
    """

    def __init__(self, log_func):
        self.user_data_dir = USER_DATA_DIR
        self.score_file = USER_DATA_DIR / "high_score.json"  # 已将最高分记录由user_data/README.md改为user_data/high_score.json
        self.old_readme_file = USER_DATA_DIR / "README.md"
        self.old_high_score_file = USER_DATA_DIR / "high_score.txt"
        self.log = log_func

    def load(self):
        """读取最高分。

        以 JSON 存档为主，旧版 README.md 和 high_score.txt 还在时取三者较大值，
        避免迁移过程中意外把玩家旧记录降成 0。
        """
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            return max(
                self._load_json_high_score(),
                self._load_old_readme_high_score(),
                self._load_old_high_score(),
            )
        except (OSError, ValueError) as exc:
            self.log(f"读取最高分失败: {exc}")
            return 0

    def save(self, score):
        """把最高分写进 JSON 存档。"""
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            with open(self.score_file, "w", encoding="utf-8") as f:
                json.dump({"high_score": int(score)}, f, ensure_ascii=False, indent=2)
                f.write("\n")
        except OSError as exc:
            self.log(f"保存最高分失败: {exc}")

    def _load_json_high_score(self):
        """读取 JSON 存档；文件损坏时当作没有记录，不影响本次游玩。"""
        if not os.path.exists(self.score_file):
            return 0

        try:
            with open(self.score_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return max(0, int(data.get("high_score", 0)))
        except (json.JSONDecodeError, AttributeError, TypeError, ValueError) as exc:
            self.log(f"最高分存档格式异常，已忽略: {exc}")
            return 0

    def _load_old_readme_high_score(self):
        """读取旧版 README.md 里的记录行，用于兼容迁移前的存档。"""
        if not os.path.exists(self.old_readme_file):
            return 0

        with open(self.old_readme_file, "r", encoding="utf-8") as f:
            match = re.search(r"无尽模式最高记录:\s*(\d+)", f.read())

        return max(0, int(match.group(1))) if match else 0

    def _load_old_high_score(self):
        """读取旧版 high_score.txt，用于兼容迁移前的存档。"""
        if not os.path.exists(self.old_high_score_file):
            return 0

        with open(self.old_high_score_file, "r", encoding="utf-8") as f:
            return max(0, int(f.read().strip() or 0))


class LevelProgressStore:
    """关卡进度存储器。"""

    def __init__(self, log_func):
        self.progress_file = USER_DATA_DIR / "level_progress.json"
        self.log = log_func

    def load(self):
        """读取已通关关卡集合。"""
        try:
            if not os.path.exists(self.progress_file):
                return set()
            with open(self.progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return set(int(l) for l in data.get("completed_levels", []))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.log(f"读取关卡进度失败: {exc}")
            return set()

    def save(self, completed_levels):
        """保存已通关关卡集合。"""
        try:
            os.makedirs(USER_DATA_DIR, exist_ok=True)
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(
                    {"completed_levels": sorted(completed_levels)},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
                f.write("\n")
        except OSError as exc:
            self.log(f"保存关卡进度失败: {exc}")
