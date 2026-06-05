import logging
import sys
from pathlib import Path
from types import FrameType
from typing import cast

from loguru import logger

from core.config import settings


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = cast(FrameType, frame.f_back)
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logger():
    logger.remove()

    log_level = settings.logging.level.upper()
    log_file = settings.logging.file
    disable_access_log = settings.logging.disable_access_log

    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            level=log_level,
            rotation="500 MB",
            retention="10 days",
            compression="zip",
            enqueue=True,
        )

    logging.getLogger().handlers = [InterceptHandler()]
    for logger_name in ("uvicorn.asgi", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.disabled = disable_access_log
        uvicorn_logger.handlers = [InterceptHandler()]


setup_logger()
