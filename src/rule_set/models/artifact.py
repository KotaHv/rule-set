from enum import StrEnum

from pydantic import BaseModel


class ArtifactKind(StrEnum):
    DEFAULT = "default"
    DOMAIN = "domain"
    IPCIDR = "ipcidr"
    CLASSICAL = "classical"


class Artifact(BaseModel):
    kind: ArtifactKind
    data: str | bytes
