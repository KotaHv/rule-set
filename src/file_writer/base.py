from abc import ABC, abstractmethod
from pathlib import Path

from config import DIR_PATH
from .write import write


class BaseFileWriter(ABC):
    def __init__(self, *, data: str, target_path: Path) -> None:
        self.data = data
        self.filepath = DIR_PATH / self.base_path / target_path.with_suffix(self.suffix)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    @property
    @abstractmethod
    def base_path(self) -> str: ...

    @property
    @abstractmethod
    def suffix(self) -> str: ...

    def write(self):
        write(self.filepath, self.data)
