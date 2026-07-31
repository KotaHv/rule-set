import json
from collections.abc import Iterable
from pathlib import Path

from .config import settings


class MetadataStore:
    def __init__(self) -> None:
        self.path = settings.metadata_path
        self.data: dict[str, float] = (
            json.loads(self.path.read_text(encoding="utf-8"))
            if self.path.exists()
            else {}
        )
        self.changed = False

    def update(self, paths: Iterable[Path], timestamp: float) -> None:
        for path in paths:
            key = path.relative_to(settings.build_dir).as_posix()
            if self.data.get(key) != timestamp:
                self.data[key] = timestamp
                self.changed = True

    def save(self) -> None:
        if self.changed:
            self.path.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
