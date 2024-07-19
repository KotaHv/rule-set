import hashlib

from pathlib import Path
from typing import Any

from loguru import logger


class Cache:
    def __init__(self, *, path: Path | str) -> None:
        self.cache_directory = Path(".cache") / Path(path)
        self.cache_directory.mkdir(exist_ok=True, parents=True)

    @staticmethod
    def generate_cache_key(key: Any) -> str:
        return hashlib.sha256(str(key).encode()).hexdigest()

    def retrieve(self, key: Any, as_bytes: bool = False) -> str | bytes | None:
        filepath = self.get_file_path(key)
        mode = "rb" if as_bytes else "r"
        try:
            with filepath.open(mode) as file:
                cache_content = file.read()
                if cache_content:
                    logger.success(f'Cache hit for key "{key}" at "{filepath}"')
                    return cache_content
                else:
                    logger.info(f'Cache file for key "{key}" is empty: "{filepath}"')
        except FileNotFoundError:
            logger.info(f'Cache miss for key "{key}": "{filepath}"')
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
        hash_key = self.generate_cache_key(key)
        return self.cache_directory / hash_key
