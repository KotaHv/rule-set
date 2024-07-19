from .base import BaseFileWriter


class FileWriter(BaseFileWriter):
    @property
    def base_path(self) -> str:
        return "Surge"

    @property
    def suffix(self) -> str:
        return ".list"
