from .base import BaseFileWriter
from .middleware import PostWriteMiddleware, SingBoxCompileMiddleware


class SingBoxFileWriter(BaseFileWriter):
    @property
    def base_path(self) -> str:
        return "sing-box"

    @property
    def suffix(self) -> str:
        return ".json"

    @property
    def post_write_middlewares(self) -> list[PostWriteMiddleware]:
        return [SingBoxCompileMiddleware(self.metadata_store)]
