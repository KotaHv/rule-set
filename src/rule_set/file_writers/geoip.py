from .base import BaseFileWriter
from .middleware import MetadataMiddleware


class GeoIPFileWriter(BaseFileWriter):
    @property
    def base_path(self) -> str:
        return "geoip"

    @property
    def suffix(self) -> str:
        return ".dat"

    @property
    def middlewares(self):
        return [MetadataMiddleware(self.metadata_store)]
