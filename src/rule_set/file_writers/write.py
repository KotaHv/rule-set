from pathlib import Path

from loguru import logger


def write(filepath: Path, data: str | bytes) -> None:
    if isinstance(data, bytes):
        with filepath.open(mode="wb") as file:
            file.write(data)
    else:
        with filepath.open(mode="w", encoding="utf-8") as file:
            file.write(data)
    logger.success(f"{filepath} generated successfully")
