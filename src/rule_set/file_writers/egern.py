from .base import BaseFileWriter


class EgernFileWriter(BaseFileWriter):
    @property
    def base_path(self) -> str:
        return "egern"

    @property
    def suffix(self) -> str:
        return ".yaml"
