from .base import BaseFileWriter
from .middleware import MihomoCompileMiddleware


class BaseClashFileWriter(BaseFileWriter):
    behavior: str

    @property
    def base_path(self) -> str:
        return f"clash/{self.behavior}"

    @property
    def suffix(self) -> str:
        return ".yaml"


class ClashDomainFileWriter(BaseClashFileWriter):
    behavior = "domain"

    @property
    def post_write_middlewares(self):
        return [MihomoCompileMiddleware(self.behavior, self.metadata_store)]


class ClashIpcidrFileWriter(BaseClashFileWriter):
    behavior = "ipcidr"

    @property
    def post_write_middlewares(self):
        return [MihomoCompileMiddleware(self.behavior, self.metadata_store)]


class ClashClassicalFileWriter(BaseClashFileWriter):
    behavior = "classical"
