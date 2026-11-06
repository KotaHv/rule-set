from typing import override

from .base import BaseFileWriter
from .middleware import MihomoMrsMiddleware, PostWriteMiddleware


class BaseClashFileWriter(BaseFileWriter):
    behavior: str

    @property
    @override
    def base_path(self) -> str:
        return f"clash/{self.behavior}"

    @property
    @override
    def suffix(self) -> str:
        return ".yaml"


class ClashDomainFileWriter(BaseClashFileWriter):
    behavior: str = "domain"

    @property
    @override
    def post_write_middlewares(self) -> list[PostWriteMiddleware]:
        return [MihomoMrsMiddleware("domain", self.metadata_store)]


class ClashIpcidrFileWriter(BaseClashFileWriter):
    behavior: str = "ipcidr"

    @property
    @override
    def post_write_middlewares(self) -> list[PostWriteMiddleware]:
        return [MihomoMrsMiddleware("ipcidr", self.metadata_store)]


class ClashClassicalFileWriter(BaseClashFileWriter):
    behavior: str = "classical"
