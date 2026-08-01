from .base import BaseFileWriter
from .middleware import SingBoxCompileMiddleware


class SingBoxFileWriter(BaseFileWriter):
    @property
    def base_path(self) -> str:
        return "sing-box"

    @property
    def suffix(self) -> str:
        return ".json"

    @property
    def post_write_middlewares(self):
        return [SingBoxCompileMiddleware(self.metadata_store)]
