import os
import secrets
import stat
from contextlib import suppress
from pathlib import Path

from loguru import logger


def _content_changed(filepath: Path, data: str | bytes) -> bool:
    if not filepath.exists():
        return True
    if isinstance(data, bytes):
        return data != filepath.read_bytes()
    existing_lines = filepath.read_text(encoding="utf-8").splitlines()
    generated_lines = data.splitlines()
    if len(generated_lines) != len(existing_lines):
        return True
    for generated_line, existing_line in zip(
        generated_lines, existing_lines, strict=False
    ):
        if generated_line.startswith("# Last Updated:") and existing_line.startswith(
            "# Last Updated:"
        ):
            continue
        if generated_line != existing_line:
            return True
    return False


def _write(filepath: Path, data: str | bytes) -> None:
    temp_path = filepath.with_name(f".{filepath.name}.{secrets.token_hex(8)}.tmp")
    try:
        if isinstance(data, bytes):
            with temp_path.open(mode="wb") as file:
                _ = file.write(data)
        else:
            with temp_path.open(mode="w", encoding="utf-8") as file:
                _ = file.write(data)

        if filepath.exists():
            temp_path.chmod(stat.S_IMODE(filepath.stat().st_mode))

        os.replace(temp_path, filepath)
    except BaseException:
        with suppress(OSError):
            temp_path.unlink(missing_ok=True)
        raise

    logger.success(f"{filepath} generated successfully")


def write_if_changed(filepath: Path, data: str | bytes) -> bool:
    if not data:
        return False
    if not _content_changed(filepath, data):
        return False
    filepath.parent.mkdir(parents=True, exist_ok=True)
    _write(filepath, data)
    return True
