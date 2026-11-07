import sqlite3
from pathlib import Path
from types import TracebackType

from pydantic import TypeAdapter, ValidationError

from .config import settings
from .models.metadata import MetadataRecord

_LEGACY_METADATA = TypeAdapter(dict[str, float])
_METADATA_ROWS = TypeAdapter(list[tuple[str, float]])


class MetadataStore:
    def __init__(self) -> None:
        self.path: Path = settings.metadata_path
        self.legacy_path: Path = self.path.with_suffix(".json")
        needs_migration = not self.path.exists()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection: sqlite3.Connection = sqlite3.connect(self.path)
        with self.connection:
            _ = self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    path TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL
                )
                """
            )
        if needs_migration and self.legacy_path.exists():
            self._migrate_legacy_json()
            self.legacy_path.unlink()

    def _migrate_legacy_json(self) -> None:
        try:
            data = _LEGACY_METADATA.validate_json(
                self.legacy_path.read_text(encoding="utf-8")
            )
        except ValidationError as error:
            raise ValueError(
                f"Metadata must contain a JSON object: {self.legacy_path}"
            ) from error
        with self.connection:
            _ = self.connection.executemany(
                """
                INSERT INTO metadata (path, timestamp)
                VALUES (?, ?)
                ON CONFLICT(path) DO UPDATE SET timestamp = excluded.timestamp
                """,
                data.items(),
            )

    def __enter__(self) -> MetadataStore:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    @property
    def data(self) -> list[MetadataRecord]:
        rows = _METADATA_ROWS.validate_python(
            self.connection.execute("SELECT path, timestamp FROM metadata").fetchall()
        )
        return [
            MetadataRecord(path=Path(path), timestamp=timestamp)
            for path, timestamp in rows
        ]

    def update(self, record: MetadataRecord) -> None:
        relative_path = record.path.relative_to(settings.build_dir).as_posix()
        with self.connection:
            _ = self.connection.execute(
                """
                INSERT INTO metadata (path, timestamp)
                VALUES (?, ?)
                ON CONFLICT(path) DO UPDATE SET timestamp = excluded.timestamp
                WHERE timestamp != excluded.timestamp
                """,
                (relative_path, record.timestamp),
            )

    def close(self) -> None:
        self.connection.close()
