import hashlib
from pathlib import Path


class Cache:
    def __init__(self, *, path: Path | str) -> None:
        self.path = Path(".cache") / path
        self.path.mkdir(exist_ok=True, parents=True)

    @staticmethod
    def generate_key(key: str):
        return hashlib.sha256(key.encode()).hexdigest()

    def get(self, key: str) -> str | None:
        key = self.generate_key(key)
        filepath = self.path / key
        try:
            with filepath.open() as f:
                cache = f.read()
                if cache:
                    return cache
        except FileNotFoundError:
            return None

    def set(self, key: str, value: str):
        key = self.generate_key(key)
        filepath = self.path / key
        with filepath.open("w") as f:
            f.write(value)
