import json
import os
import tempfile
from collections.abc import Iterable
from pathlib import Path

from .config import settings


class MetadataStore:
    def __init__(self) -> None:
        self.path = settings.metadata_path
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise ValueError(f"Failed to load metadata from {self.path}") from error
            if not isinstance(data, dict):
                raise ValueError(f"Metadata must contain a JSON object: {self.path}")
            self.data = data
        else:
            self.data = {}
        self.changed = False

    def update(self, paths: Iterable[Path], timestamp: float) -> None:
        for path in paths:
            key = path.relative_to(settings.build_dir).as_posix()
            if self.data.get(key) != timestamp:
                self.data[key] = timestamp
                self.changed = True

    def save(self) -> None:
        if not self.changed:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_file = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            delete=False,
        )
        temporary_path = Path(temporary_file.name)
        try:
            with temporary_file:
                temporary_file.write(
                    json.dumps(self.data, ensure_ascii=False, indent=2) + "\n"
                )
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, self.path)
            directory_fd = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
