from typing import List, Annotated, Set
from enum import Enum

from pydantic import BaseModel, HttpUrl, BeforeValidator


class ClientEnum(str, Enum):
    Surge = "Surge"
    Loon = "Loon"
    Egern = "Egern"
    Clash = "Clash"
    Sing_Box = "sing-box"


Url = Annotated[str, HttpUrl]

Urls = Annotated[
    List[Url],
    BeforeValidator(lambda x: [x] if isinstance(x, str) else x),
    List[HttpUrl],
]

ClientEnums = Annotated[
    List[ClientEnum],
    BeforeValidator(lambda x: [x] if isinstance(x, ClientEnum) else x),
]


class SourceModel(BaseModel):
    urls: Urls
    filename: str
    exclude: ClientEnums = []
    include: ClientEnums | None = None
    no_resolve: bool = True

    def __repr__(self) -> str:
        if len(self.urls) == 1:
            return f'{self.filename}: "{self.urls[0]}"'
        return f"{self.filename}: {self.urls}"

    def __str__(self) -> str:
        return self.__repr__()


class RuleModel(BaseModel):
    domain: Set[str] | List[str] = set()
    domain_suffix: Set[str] | List[str] = set()
    domain_keyword: Set[str] | List[str] = set()
    domain_wildcard: Set[str] | List[str] = set()
    ip_cidr: Set[str] | List[str] = set()
    ip_cidr6: Set[str] | List[str] = set()
    ip_asn: Set[str] | List[str] = set()
    logical: Set[str] | List[str] = set()
    process: Set[str] | List[str] = set()
    ua: Set[str] | List[str] = set()

    def merge_with(self, other: "RuleModel") -> None:
        self.domain.update(other.domain)
        self.domain_suffix.update(other.domain_suffix)
        self.domain_keyword.update(other.domain_keyword)
        self.domain_wildcard.update(other.domain_wildcard)
        self.ip_cidr.update(other.ip_cidr)
        self.ip_cidr6.update(other.ip_cidr6)
        self.ip_asn.update(other.ip_asn)
        self.logical.update(other.logical)
        self.process.update(other.process)
        self.ua.update(other.ua)
