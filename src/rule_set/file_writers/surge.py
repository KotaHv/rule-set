from .base import BaseFileWriter
from .middleware import MetadataMiddleware


class SurgeFileWriter(BaseFileWriter):
    @property
    def base_path(self) -> str:
        return "surge"

    @property
    def suffix(self) -> str:
        return ".list"

    @property
    def middlewares(self):
        return [MetadataMiddleware(self.metadata_store)]
