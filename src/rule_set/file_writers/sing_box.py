from .base import BaseFileWriter
from .middleware import MetadataMiddleware, SingBoxCompileMiddleware


class SingBoxFileWriter(BaseFileWriter):
    @property
    def base_path(self) -> str:
        return "sing-box"

    @property
    def suffix(self) -> str:
        return ".json"

    @property
    def middlewares(self):
        return [
            SingBoxCompileMiddleware(),
            MetadataMiddleware(self.metadata_store),
        ]
