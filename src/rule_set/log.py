import sys
from typing import Any, TypedDict

from loguru import logger

from .config import settings


class _LogRecord(TypedDict):
    extra: dict[str, Any]


def _log_format(record: _LogRecord) -> str:
    context = "<cyan>[{extra[source]}]</cyan> " if record["extra"].get("source") else ""
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        + "<level>{level: <8}</level> | "
        + "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        + context
        + "<level>{message}</level>\n{exception}"
    )


def setup_logging() -> None:
    logger.remove()
    _ = logger.add(sys.stderr, level=settings.log_level, format=_log_format)
