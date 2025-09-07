from pathlib import Path

from loguru import logger


def write(filepath: Path, data: str | bytes):
    mode = "wb" if isinstance(data, bytes) else "w"
    try:
        with filepath.open(mode=mode) as file:
            file.write(data)
        logger.success(f"{filepath} generated successfully")
    except Exception as e:
        logger.error(f"Failed to write to {filepath}: {e}")
