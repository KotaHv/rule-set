from typing import override

from .base import BaseFileWriter


class EgernFileWriter(BaseFileWriter):
    @property
    @override
    def base_path(self) -> str:
        return "egern"

    @property
    @override
    def suffix(self) -> str:
        return ".yaml"
