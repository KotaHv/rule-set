from abc import ABC, abstractmethod
from pathlib import Path

from rule_set.config import settings
from rule_set.metadata import MetadataStore
from rule_set.models import WriteContext

from .middleware import MetadataMiddleware, PostWriteMiddleware, PreWriteMiddleware
from .write import write


class BaseFileWriter(ABC):
    def __init__(
        self,
        *,
        data: str | bytes,
        target_path: Path,
        timestamp: float,
        metadata_store: MetadataStore,
    ) -> None:
        self.data = data
        self.timestamp = timestamp
        self.metadata_store = metadata_store
        self.filepath = (
            settings.build_dir / self.base_path / target_path.with_suffix(self.suffix)
        )

    @property
    @abstractmethod
    def base_path(self) -> str: ...

    @property
    @abstractmethod
    def suffix(self) -> str: ...

    @property
    def post_write_middlewares(self) -> list[PostWriteMiddleware]:
        return []

    @property
    def pre_write_middlewares(self) -> list[PreWriteMiddleware]:
        return [MetadataMiddleware(self.metadata_store)]

    def has_changes(self) -> bool:
        if self.filepath.exists():
            if isinstance(self.data, bytes):
                return self.data != self.filepath.read_bytes()
            existing_lines = self.filepath.read_text(encoding="utf-8").splitlines()
            generated_lines = self.data.splitlines()
            if len(generated_lines) != len(existing_lines):
                return True
            for generated_line, existing_line in zip(
                generated_lines, existing_lines, strict=False
            ):
                if generated_line.startswith(
                    "# Last Updated:"
                ) and existing_line.startswith("# Last Updated:"):
                    continue
                if generated_line != existing_line:
                    return True
            return False
        return True

    def write(self) -> bool:
        if not self.data or not self.has_changes():
            return False
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        context = WriteContext(
            filepath=self.filepath,
            timestamp=self.timestamp,
        )
        for middleware in self.pre_write_middlewares:
            middleware.before_write(context)
        write(self.filepath, self.data)
        for middleware in self.post_write_middlewares:
            middleware.after_write(context)
        return True
