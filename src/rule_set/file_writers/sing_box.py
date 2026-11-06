from typing import override

from .base import BaseFileWriter
from .middleware import PostWriteMiddleware, SingBoxSrsMiddleware


class SingBoxFileWriter(BaseFileWriter):
    @property
    @override
    def base_path(self) -> str:
        return "sing-box"

    @property
    @override
    def suffix(self) -> str:
        return ".json"

    @property
    @override
    def post_write_middlewares(self) -> list[PostWriteMiddleware]:
        return [SingBoxSrsMiddleware(self.metadata_store)]
