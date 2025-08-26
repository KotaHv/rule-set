from pydantic import BaseModel, field_validator

from .enum import V2rayAttrMode


class V2rayDomainAttr(BaseModel):
    mode: V2rayAttrMode
    attrs: list[str] = []

    @classmethod
    def ALL(cls) -> "V2rayDomainAttr":
        return cls(mode=V2rayAttrMode.ALL)

    @classmethod
    def NO_ATTR(cls) -> "V2rayDomainAttr":
        return cls(mode=V2rayAttrMode.NO_ATTR)

    @classmethod
    def ATTRS(cls, attr: str | list[str]) -> "V2rayDomainAttr":
        return cls(
            mode=V2rayAttrMode.ATTRS,
            attrs=[attr] if isinstance(attr, str) else attr,
        )

    @classmethod
    def EXCLUDE_ATTRS(cls, attr: str | list[str]) -> "V2rayDomainAttr":
        return cls(
            mode=V2rayAttrMode.EXCLUDE_ATTRS,
            attrs=[attr] if isinstance(attr, str) else attr,
        )

    @field_validator("attrs")
    @classmethod
    def ensure_at_prefix(cls, v: list[str]) -> list[str]:
        result = []
        for a in v:
            a = a.strip()
            if not a.startswith("@"):
                a = f"@{a}"
            if a not in result:
                result.append(a)
        return result

    def filter_attrs(self, rule_attrs: list[str]) -> bool:
        if self.mode == V2rayAttrMode.ALL:
            return True
        elif self.mode == V2rayAttrMode.NO_ATTR:
            return len(rule_attrs) == 0
        elif self.mode == V2rayAttrMode.ATTRS:
            if not rule_attrs:
                return False
            return bool(set(rule_attrs) & set(self.attrs))
        elif self.mode == V2rayAttrMode.EXCLUDE_ATTRS:
            if not rule_attrs:
                return True
            return not bool(set(rule_attrs) & set(self.attrs))
        return False

    def __repr__(self) -> str:
        if self.mode == V2rayAttrMode.ATTRS:
            return f"ATTRS<{'|'.join(self.attrs)}>"
        if self.mode == V2rayAttrMode.EXCLUDE_ATTRS:
            return f"EXCLUDE_ATTRS<{'|'.join(self.attrs)}>"
        return self.mode.value

    def __str__(self) -> str:
        return self.__repr__()


class SerializationOption(BaseModel):
    no_resolve: bool = True
    clash_optimize: bool = True


class ProcessingOption(BaseModel):
    exclude_rule_types: list[str] = []
    optimize_domains: bool = False
    exclude_optimized_domains: list[str] = []
    exclude_keywords: list[str] = []
    exclude_suffixes: list[str] = []


class V2rayDomainOption(BaseModel):
    attrs: V2rayDomainAttr | None = None
    exclude_includes: list[str] | None = None


class GeoIPOption(BaseModel):
    country_code: str | None = None


class Option(BaseModel):
    """Unified configuration option container"""

    serialization: SerializationOption = SerializationOption()
    processing: ProcessingOption = ProcessingOption()
    v2ray_domain: V2rayDomainOption = V2rayDomainOption(
        attrs=V2rayDomainAttr.ALL(), exclude_includes=[]
    )
    geo_ip: GeoIPOption = GeoIPOption()

    @field_validator("v2ray_domain", mode="before")
    def set_default_v2ray_domain_option(cls, v: V2rayDomainOption) -> V2rayDomainOption:
        """Set default values for V2rayDomainOption fields if they are None."""
        if v.attrs is None:
            v.attrs = V2rayDomainAttr.ALL()
        if v.exclude_includes is None:
            v.exclude_includes = []
        return v
