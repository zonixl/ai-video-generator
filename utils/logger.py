"""统一日志初始化。

用法：
    from utils.logger import setup_logging
    setup_logging(cfg, debug=True)   # 控制台 DEBUG
    setup_logging(cfg, debug=False)  # 控制台 INFO
"""

import logging
import sys
from pathlib import Path


def setup_logging(cfg, debug: bool = False) -> logging.Logger:
    """配置全局日志：控制台 + 文件双输出。

    - debug=True  → 控制台 DEBUG，日志文件 DEBUG
    - debug=False → 控制台 INFO，日志文件按 cfg.logging_file_level 决定（默认 DEBUG）
    """
    console_level = logging.DEBUG if debug else getattr(logging, cfg.logging_level.upper(), logging.INFO)
    file_level = getattr(logging, cfg.logging_file_level.upper(), logging.DEBUG)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # root 设最低，具体级别由 handler 控制

    # 移除已有的 handler（避免重复添加）
    root.handlers.clear()

    formatter = logging.Formatter(
        fmt=cfg.logging_format,
        datefmt=cfg.logging_datefmt,
    )

    # 控制台 handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(console_level)
    console.setFormatter(formatter)
    root.addHandler(console)

    # 文件 handler（DEBUG 全量持久化）
    file_path = Path(cfg.logging_file)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(str(file_path), encoding="utf-8")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    logger = logging.getLogger("pipeline")
    logger.debug("Logging initialized (console=%s, file=%s, file_path=%s)",
                 logging.getLevelName(console_level),
                 logging.getLevelName(file_level),
                 file_path)
    return logger
