"""全局配置。

为什么不用 pydantic-settings 或者 configparser？
—— 这个项目的配置项不到 10 个，全部来自环境变量就够了。
   少一个依赖、少一层抽象，读代码的人 10 秒就能看懂全部配置。

设置方式：在项目根目录放一个 .env（参考 .env.example），或者直接设环境变量。
.env 由下面那行 load_dotenv 加载，优先级低于真实环境变量（环境变量里已有的不会被覆盖）。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录：app/config.py -> app/ -> 项目根
BASE_DIR = Path(__file__).resolve().parent.parent

# 把项目根目录下的 .env 读进环境变量。文件不存在时什么都不做，也不报错。
# 必须写在任何 os.getenv 之前，所以放在模块顶层。
load_dotenv(BASE_DIR / ".env")


def _default_db_path() -> Path:
    return BASE_DIR / "data" / "documind.db"


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:  # 配置写错时给出明确报错，而不是默默用默认值
        raise ValueError(f"环境变量 {name} 必须是整数，当前值：{raw!r}") from exc


@dataclass(frozen=True)
class Settings:
    """一次运行期间不变化的配置。frozen=True 防止运行中被意外改动。"""

    db_path: Path = field(default_factory=_default_db_path)
    chunk_size: int = 500
    chunk_overlap: int = 80
    top_k: int = 5
    embedding_dim: int = 256
    max_upload_bytes: int = 5 * 1024 * 1024


def load_settings() -> Settings:
    """从环境变量读取配置，缺省时使用默认值。"""
    return Settings(
        db_path=Path(os.getenv("DOCUMIND_DB") or _default_db_path()),
        chunk_size=_env_int("DOCUMIND_CHUNK_SIZE", 500),
        chunk_overlap=_env_int("DOCUMIND_CHUNK_OVERLAP", 80),
        top_k=_env_int("DOCUMIND_TOP_K", 5),
        embedding_dim=_env_int("DOCUMIND_EMBED_DIM", 256),
        max_upload_bytes=_env_int("DOCUMIND_MAX_UPLOAD", 5 * 1024 * 1024),
    )
