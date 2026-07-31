from .base import BaseFileWriter
from .middleware import MetadataMiddleware, MihomoCompileMiddleware


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
    def middlewares(self):
        return [
            MihomoCompileMiddleware(self.behavior),
            MetadataMiddleware(self.metadata_store),
        ]


class ClashIpcidrFileWriter(BaseClashFileWriter):
    behavior = "ipcidr"

    @property
    def middlewares(self):
        return [
            MihomoCompileMiddleware(self.behavior),
            MetadataMiddleware(self.metadata_store),
        ]


class ClashClassicalFileWriter(BaseClashFileWriter):
    behavior = "classical"

    @property
    def middlewares(self):
        return [MetadataMiddleware(self.metadata_store)]
