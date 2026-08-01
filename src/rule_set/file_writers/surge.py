from .base import BaseFileWriter


class SurgeFileWriter(BaseFileWriter):
    @property
    def base_path(self) -> str:
        return "surge"

    @property
    def suffix(self) -> str:
        return ".list"
