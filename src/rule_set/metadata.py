import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from .config import settings


class MetadataStore:
    def __init__(self) -> None:
        self.path = settings.metadata_path
        self.legacy_path = self.path.with_suffix(".json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    path TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL
                )
                """
            )
        if self.legacy_path.exists():
            self._migrate_legacy_json()
            self.legacy_path.unlink()

    def _migrate_legacy_json(self) -> None:
        data = json.loads(self.legacy_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"Metadata must contain a JSON object: {self.legacy_path}")
        with self.connection:
            self.connection.executemany(
                """
                INSERT INTO metadata (path, timestamp)
                VALUES (?, ?)
                ON CONFLICT(path) DO UPDATE SET timestamp = excluded.timestamp
                """,
                data.items(),
            )

    @property
    def data(self) -> dict[str, float]:
        return dict(self.connection.execute("SELECT path, timestamp FROM metadata"))

    def update(self, paths: Iterable[Path], timestamp: float) -> None:
        rows = [
            (path.relative_to(settings.build_dir).as_posix(), timestamp)
            for path in paths
        ]
        if not rows:
            return
        with self.connection:
            self.connection.executemany(
                """
                INSERT INTO metadata (path, timestamp)
                VALUES (?, ?)
                ON CONFLICT(path) DO UPDATE SET timestamp = excluded.timestamp
                WHERE timestamp != excluded.timestamp
                """,
                rows,
            )
