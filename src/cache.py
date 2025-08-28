from pathlib import Path
from typing import Any
from datetime import datetime, timedelta

from loguru import logger

from utils import generate_cache_key
from config import settings


class Cache:
    def __init__(self, *, path: Path | str, ttl_hours: int | None = None) -> None:
        self.cache_directory = settings.cache_dir / Path(path)
        self.cache_directory.mkdir(exist_ok=True, parents=True)
        self.ttl_hours = ttl_hours or settings.cache_ttl_hours

        # Automatically clean up expired files on initialization
        self.clear_expired()

    def retrieve(self, key: Any, as_bytes: bool = False) -> str | bytes | None:
        filepath = self.get_file_path(key)
        mode = "rb" if as_bytes else "r"

        try:
            # Check if file exists and is not expired
            if not filepath.exists():
                logger.info(f'Cache miss for key "{key}": "{filepath}"')
                return None

            # Check file modification time
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            if datetime.now() - mtime > timedelta(hours=self.ttl_hours):
                logger.info(
                    f'Cache expired for key "{key}" at "{filepath}" (modified: {mtime})'
                )
                # Remove expired cache file
                filepath.unlink(missing_ok=True)
                return None

            with filepath.open(mode) as file:
                cache_content = file.read()
                if cache_content:
                    logger.success(f'Cache hit for key "{key}" at "{filepath}"')
                    return cache_content
                else:
                    logger.info(f'Cache file for key "{key}" is empty: "{filepath}"')
        except FileNotFoundError:
            logger.info(f'Cache miss for key "{key}": "{filepath}"')
        except Exception as e:
            logger.warning(f'Error reading cache for key "{key}": {e}')
        return None

    def store(self, key: Any, value: str | bytes) -> Path:
        filepath = self.get_file_path(key)
        try:
            if isinstance(value, bytes):
                with filepath.open("wb") as file:
                    file.write(value)
            else:
                with filepath.open("w") as file:
                    file.write(value)
            logger.success(f'Successfully cached key "{key}" at "{filepath}"')
        except Exception as e:
            logger.error(f'Failed to cache key "{key}" at "{filepath}": {e}')
        return filepath

    def get_file_path(self, key: Any) -> Path:
        hash_key = generate_cache_key(key)
        return self.cache_directory / hash_key

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
                        filepath.unlink()
                        removed_count += 1
                        logger.debug(f"Removed expired cache file: {filepath}")
                except Exception as e:
                    logger.warning(f"Error checking cache file {filepath}: {e}")

        if removed_count > 0:
            logger.info(
                f"Cleared {removed_count} expired cache files from {self.cache_directory}"
            )

        return removed_count
