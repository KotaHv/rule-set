from typing import override

from pydantic import BaseModel, field_validator

from .enum import ProcessingRuleType


class V2rayDomainAttrs(BaseModel):
    include_attrs: list[str] = []
    exclude_attrs: list[str] = []

    @field_validator("include_attrs", "exclude_attrs")
    @classmethod
    def ensure_at_prefix(cls, v: list[str]) -> list[str]:
        result: list[str] = []
        for a in v:
            a = a.strip()
            if not a.startswith("@"):
                a = f"@{a}"
            if a not in result:
                result.append(a)
        return result

    def matches(self, attrs: list[str]) -> bool:
        if not self.include_attrs:
            include_flag = True
        else:
            include_flag = bool(set(self.include_attrs) & set(attrs))
        if not self.exclude_attrs:
            exclude_flag = True
        else:
            exclude_flag = not bool(set(self.exclude_attrs) & set(attrs))
        return include_flag and exclude_flag

    @override
    def __repr__(self) -> str:
        return f"include_attrs={self.include_attrs}, exclude_attrs={self.exclude_attrs}"

    @override
    def __str__(self) -> str:
        return self.__repr__()


class SerializationOption(BaseModel):
    no_resolve: bool = True


class ProcessingOption(BaseModel):
    include_rule_types: list[ProcessingRuleType] = []
    exclude_rule_types: list[ProcessingRuleType] = []
    exclude_keywords: list[str] = []
    exclude_suffixes: list[str] = []


class V2rayDomainOption(BaseModel):
    attrs: V2rayDomainAttrs = V2rayDomainAttrs()
    exclude_includes: list[str] = []


class GeoIPOption(BaseModel):
    country_code: str | None = None


class Option(BaseModel):
    """Unified configuration option container"""

    serialization: SerializationOption = SerializationOption()
    processing: ProcessingOption = ProcessingOption()
    v2ray_domain: V2rayDomainOption = V2rayDomainOption()
    geo_ip: GeoIPOption = GeoIPOption()
