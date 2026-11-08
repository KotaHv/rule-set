from enum import StrEnum


class ArtifactKind(StrEnum):
    DOMAIN = "domain"
    IPCIDR = "ipcidr"
    CLASSICAL = "classical"
