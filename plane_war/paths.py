"""项目路径常量。

所有磁盘路径都从这里派生，模块内部不再自己拼接项目根目录。
这样源码移动到别的子包时，资源和存档的定位方式不需要跟着改。
"""

from pathlib import Path

# plane_war/paths.py 的上两级就是项目根目录。
PROJECT_ROOT = Path(__file__).resolve().parent.parent

ASSETS_DIR = PROJECT_ROOT / "assets"
PICTURES_DIR = ASSETS_DIR / "pictures"

PLANE_DIR = PICTURES_DIR / "plane"
BULLETS_DIR = PICTURES_DIR / "bullets"
METEORITE_DIR = PICTURES_DIR / "meteorite"
POWERUP_DIR = PICTURES_DIR / "powerup"
LEVEL_BUTTON_DIR = PICTURES_DIR / "level_button"

USER_DATA_DIR = PROJECT_ROOT / "user_data"
