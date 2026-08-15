"""与 pygame 无关的通用工具函数。"""


def clamp(value, minimum, maximum):
    """把数值限制在最小值和最大值之间。

    玩家位置、滑杆值等都可以用这个函数避免越界。
    """
    return max(minimum, min(maximum, value))
