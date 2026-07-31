from .base import BaseFileWriter
from .middleware import MetadataMiddleware


class LoonFileWriter(BaseFileWriter):
    @property
    def base_path(self) -> str:
        return "loon"

    @property
    def suffix(self) -> str:
        return ".list"

    @property
    def middlewares(self):
        return [MetadataMiddleware(self.metadata_store)]
