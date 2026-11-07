from typing import override

from .base import BaseFileWriter


class LoonFileWriter(BaseFileWriter):
    @property
    @override
    def base_path(self) -> str:
        return "loon"

    @property
    @override
    def suffix(self) -> str:
        return ".list"
