from typing import override

from .base import BaseFileWriter


class GeoIPFileWriter(BaseFileWriter):
    @property
    @override
    def base_path(self) -> str:
        return "geoip"

    @property
    @override
    def suffix(self) -> str:
        return ".dat"
