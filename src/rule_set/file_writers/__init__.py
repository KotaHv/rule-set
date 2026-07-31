from ..models import ArtifactKind, SerializeFormat
from .base import BaseFileWriter
from .clash import (
    ClashClassicalFileWriter,
    ClashDomainFileWriter,
    ClashIpcidrFileWriter,
)
from .egern import EgernFileWriter
from .geoip import GeoIPFileWriter
from .loon import LoonFileWriter
from .sing_box import SingBoxFileWriter
from .surge import SurgeFileWriter

writer_registry: dict[tuple[SerializeFormat, ArtifactKind], type[BaseFileWriter]] = {
    (SerializeFormat.Surge, ArtifactKind.DEFAULT): SurgeFileWriter,
    (SerializeFormat.Loon, ArtifactKind.DEFAULT): LoonFileWriter,
    (SerializeFormat.Egern, ArtifactKind.DEFAULT): EgernFileWriter,
    (SerializeFormat.Sing_Box, ArtifactKind.DEFAULT): SingBoxFileWriter,
    (SerializeFormat.GeoIP, ArtifactKind.DEFAULT): GeoIPFileWriter,
    (SerializeFormat.Clash, ArtifactKind.DOMAIN): ClashDomainFileWriter,
    (SerializeFormat.Clash, ArtifactKind.IPCIDR): ClashIpcidrFileWriter,
    (SerializeFormat.Clash, ArtifactKind.CLASSICAL): ClashClassicalFileWriter,
}

__all__ = [
    SurgeFileWriter,
    LoonFileWriter,
    ClashDomainFileWriter,
    ClashIpcidrFileWriter,
    ClashClassicalFileWriter,
    EgernFileWriter,
    SingBoxFileWriter,
    GeoIPFileWriter,
    writer_registry,
]
