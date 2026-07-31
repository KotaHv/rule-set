from .base import BaseFileWriter
from .middleware import MetadataMiddleware


class EgernFileWriter(BaseFileWriter):
    @property
    def base_path(self) -> str:
        return "egern"

    @property
    def suffix(self) -> str:
        return ".yaml"

    @property
    def middlewares(self):
        return [MetadataMiddleware(self.metadata_store)]
