import os
from contextlib import suppress
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, overload

from loguru import logger

from rule_set.config import settings

from .utils import generate_cache_key


class Cache:
    def __init__(self, *, path: Path | str, ttl_hours: int | None = None) -> None:
        self.cache_directory: Path = settings.cache_dir / Path(path)
        self.cache_directory.mkdir(exist_ok=True, parents=True)
        self.ttl_hours: int = (
            settings.cache_ttl_hours if ttl_hours is None else ttl_hours
        )

        # Automatically clean up expired files on initialization
        _ = self.clear_expired()

    def retrieve_text(self, key: str) -> str | None:
        return self._retrieve(key, as_bytes=False)

    def retrieve_bytes(self, key: str) -> bytes | None:
        return self._retrieve(key, as_bytes=True)

    def retrieve_path(self, key: str) -> Path | None:
        filepath = self._get_valid_path(key)
        if filepath is not None:
            logger.success(f'Cache hit for key "{key}" at "{filepath}"')
        return filepath

    @overload
    def _retrieve(self, key: str, *, as_bytes: Literal[False]) -> str | None: ...

    @overload
    def _retrieve(self, key: str, *, as_bytes: Literal[True]) -> bytes | None: ...

    def _retrieve(self, key: str, *, as_bytes: bool) -> str | bytes | None:
        filepath = self._get_valid_path(key)
        if filepath is None:
            return None

        try:
            if as_bytes:
                with filepath.open("rb") as file:
                    cache_content = file.read()
            else:
                with filepath.open("r", encoding="utf-8") as file:
                    cache_content = file.read()
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f'Error reading cache for key "{key}": {e}')
            return None

        if cache_content:
            logger.success(f'Cache hit for key "{key}" at "{filepath}"')
        else:
            logger.info(f'Cache file for key "{key}" is empty: "{filepath}"')
        return cache_content

    def _get_valid_path(self, key: str) -> Path | None:
        filepath = self._get_file_path(key)

        try:
            if not filepath.exists():
                logger.info(f'Cache miss for key "{key}": "{filepath}"')
                return None

            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            if datetime.now() - mtime > timedelta(hours=self.ttl_hours):
                logger.info(
                    f'Cache expired for key "{key}" at "{filepath}" (modified: {mtime})'
                )
                filepath.unlink(missing_ok=True)
                return None
        except OSError as e:
            logger.warning(f'Error checking cache for key "{key}": {e}')
            return None

        return filepath

    def store(self, key: str, value: str | bytes) -> Path | None:
        filepath = self._get_file_path(key)
        tmp_path = filepath.with_name(f".{filepath.name}.{os.getpid()}.tmp")
        try:
            if isinstance(value, bytes):
                with tmp_path.open("wb") as file:
                    _ = file.write(value)
            else:
                with tmp_path.open("w", encoding="utf-8") as file:
                    _ = file.write(value)
            _ = tmp_path.replace(filepath)
        except OSError as e:
            logger.error(f'Failed to cache key "{key}" at "{filepath}": {e}')
            with suppress(OSError):
                tmp_path.unlink(missing_ok=True)
            return None

        logger.success(f'Successfully cached key "{key}" at "{filepath}"')
        return filepath

    def _get_file_path(self, key: str) -> Path:
        return self.cache_directory / generate_cache_key(key)

    def clear_expired(self) -> int:
        """Clear all expired cache files and return count of removed files"""
        if not self.cache_directory.exists():
            return 0

        removed_count = 0
        cutoff_time = datetime.now() - timedelta(hours=self.ttl_hours)

        for filepath in self.cache_directory.iterdir():
            if filepath.is_file():
                try:
                    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                    if mtime < cutoff_time:
                        filepath.unlink(missing_ok=True)
                        removed_count += 1
                        logger.debug(f"Removed expired cache file: {filepath}")
                except OSError as e:
                    logger.warning(f"Error checking cache file {filepath}: {e}")

        if removed_count > 0:
            logger.info(
                f"Cleared {removed_count} expired cache files from {self.cache_directory}"
            )

        return removed_count
