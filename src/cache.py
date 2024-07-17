import hashlib

from pathlib import Path
from typing import Any

from loguru import logger


class Cache:
    def __init__(self, *, path: Path | str) -> None:
        self.path = Path(".cache") / path
        self.path.mkdir(exist_ok=True, parents=True)

    @staticmethod
    def generate_key(key: Any) -> str:
        return hashlib.sha256(str(key).encode()).hexdigest()

    def get(self, key: Any) -> str | None:
        hash_key = self.generate_key(key)
        filepath = self.path / hash_key
        try:
            with filepath.open() as f:
                cache = f.read()
                if cache:
                    logger.success(f'"{key}": hit "{filepath}" cache')
                    return cache
        except FileNotFoundError:
            return None

    def set(self, key: Any, value: str):
        key = self.generate_key(key)
        filepath = self.path / key
        with filepath.open("w") as f:
            f.write(value)
