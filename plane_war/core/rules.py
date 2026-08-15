"""游戏数值规则和关卡公式。

这里放“可计算的规则”，例如生成间隔、目标分数、无尽模式难度推进和最高分检查点。
主流程只消费这些函数的结果，不在循环里手写公式，方便之后统一调平衡。
"""

BASE_LEVEL_SPAWN_INTERVAL = 55
MIN_LEVEL_SPAWN_INTERVAL = 10
MIN_ENDLESS_SPAWN_INTERVAL = 15
ENDLESS_BASE_DIFFICULTY = 90
ENDLESS_DIFFICULTY_INCREASE_INTERVAL = 600
ENDLESS_SPAWN_INTERVAL_STEP = 3
HIGH_SCORE_CHECKPOINT_STEP = 1000


def calculate_level_spawn_interval(level):
    """根据关卡号计算陨石生成间隔。

    每 10 关生成间隔减少 5 帧，但不会低于关卡模式的最小间隔。
    """
    return max(MIN_LEVEL_SPAWN_INTERVAL, BASE_LEVEL_SPAWN_INTERVAL - (level - 1) // 10 * 5)


def calculate_score_target(level):
    """计算关卡通关目标分数。

    第 1 关需要 1000 分，之后每关目标增加 1000 分。
    """
    return 1000 + (level - 1) * 1000


def calculate_endless_difficulty(spawn_interval):
    """把无尽模式生成间隔换算成 1 到 10 的显示难度。"""
    difficulty = int(1 + (BASE_LEVEL_SPAWN_INTERVAL - spawn_interval) / (BASE_LEVEL_SPAWN_INTERVAL - MIN_ENDLESS_SPAWN_INTERVAL) * 9)
    return max(1, min(10, difficulty))


def increase_endless_difficulty(difficulty, spawn_interval):
    """推进一次无尽模式难度，并降低陨石生成间隔。"""
    return difficulty + 1, max(MIN_ENDLESS_SPAWN_INTERVAL, spawn_interval - ENDLESS_SPAWN_INTERVAL_STEP)


def calculate_next_high_score_checkpoint(score):
    """计算下一个最高分刷新检查点。

    最高分不会每一帧都写入磁盘，而是在超过旧记录后按 1000 分台阶刷新。
    """
    return (score // HIGH_SCORE_CHECKPOINT_STEP + 1) * HIGH_SCORE_CHECKPOINT_STEP


def should_update_high_score_checkpoint(score, previous_high_score, checkpoint):
    """判断当前分数是否应该刷新一次无尽模式最高分。"""
    return score > previous_high_score and score >= checkpoint
