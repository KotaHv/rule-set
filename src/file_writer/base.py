from abc import ABC, abstractmethod
from pathlib import Path

from config import settings
from .write import write


class BaseFileWriter(ABC):
    def __init__(self, *, data: str | bytes, target_path: Path) -> None:
        self.data = data
        self.filepath = (
            settings.build_dir / self.base_path / target_path.with_suffix(self.suffix)
        )

    @property
    @abstractmethod
    def base_path(self) -> str: ...

    @property
    @abstractmethod
    def suffix(self) -> str: ...

    def write(self):
        if self.data:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            write(self.filepath, self.data)
