"""游戏数值规则和关卡公式。

把生成间隔、目标分数和无尽模式难度推进放在这里，主流程只消费结果。
"""

BASE_LEVEL_SPAWN_INTERVAL = 55
MIN_LEVEL_SPAWN_INTERVAL = 10
MIN_ENDLESS_SPAWN_INTERVAL = 15
ENDLESS_BASE_DIFFICULTY = 90
ENDLESS_DIFFICULTY_INCREASE_INTERVAL = 1000
ENDLESS_SPAWN_INTERVAL_STEP = 2
HIGH_SCORE_CHECKPOINT_STEP = 1000


def calculate_level_spawn_interval(level):
    return max(MIN_LEVEL_SPAWN_INTERVAL, BASE_LEVEL_SPAWN_INTERVAL - (level - 1) // 10 * 5)


def calculate_score_target(level):
    return 1000 + (level - 1) * 1000


def calculate_endless_difficulty(spawn_interval):
    difficulty = int(
        1
        + (BASE_LEVEL_SPAWN_INTERVAL - spawn_interval)
        / (BASE_LEVEL_SPAWN_INTERVAL - MIN_ENDLESS_SPAWN_INTERVAL)
        * 9
    )
    return max(1, min(10, difficulty))


def increase_endless_difficulty(difficulty, spawn_interval):
    return difficulty + 1, max(MIN_ENDLESS_SPAWN_INTERVAL, spawn_interval - ENDLESS_SPAWN_INTERVAL_STEP)


def calculate_next_high_score_checkpoint(score):
    return (score // HIGH_SCORE_CHECKPOINT_STEP + 1) * HIGH_SCORE_CHECKPOINT_STEP


def should_update_high_score_checkpoint(score, previous_high_score, checkpoint):
    return score > previous_high_score and score >= checkpoint
