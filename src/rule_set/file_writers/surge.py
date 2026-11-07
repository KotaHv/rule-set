from typing import override

from .base import BaseFileWriter


class SurgeFileWriter(BaseFileWriter):
    @property
    @override
    def base_path(self) -> str:
        return "surge"

    @property
    @override
    def suffix(self) -> str:
        return ".list"
