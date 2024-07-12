import hashlib
from pathlib import Path

from loguru import logger


class Cache:
    def __init__(self, *, path: Path | str) -> None:
        self.path = Path(".cache") / path
        self.path.mkdir(exist_ok=True, parents=True)

    @staticmethod
    def generate_key(key: str):
        return hashlib.sha256(key.encode()).hexdigest()

    def get(self, key: str) -> str | None:
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

    def set(self, key: str, value: str):
        key = self.generate_key(key)
        filepath = self.path / key
        with filepath.open("w") as f:
            f.write(value)
