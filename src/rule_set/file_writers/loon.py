from .base import BaseFileWriter


class LoonFileWriter(BaseFileWriter):
    @property
    def base_path(self) -> str:
        return "loon"

    @property
    def suffix(self) -> str:
        return ".list"
