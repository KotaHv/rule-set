from pydantic import BaseModel, field_validator


class V2rayDomainAttrs(BaseModel):
    include_attrs: list[str] = []
    exclude_attrs: list[str] = []

    @field_validator("include_attrs", "exclude_attrs")
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

    def filter(self, attrs: list[str]) -> bool:
        if not self.include_attrs:
            include_flag = True
        else:
            include_flag = bool(set(self.include_attrs) & set(attrs))
        if not self.exclude_attrs:
            exclude_flag = True
        else:
            exclude_flag = not bool(set(self.exclude_attrs) & set(attrs))
        return include_flag and exclude_flag

    def __repr__(self) -> str:
        return f"include_attrs={self.include_attrs}, exclude_attrs={self.exclude_attrs}"

    def __str__(self) -> str:
        return self.__repr__()


class SerializationOption(BaseModel):
    no_resolve: bool = True


class ProcessingOption(BaseModel):
    exclude_rule_types: list[str] = []
    optimize_domains: bool = False
    exclude_optimized_domains: list[str] = []
    exclude_keywords: list[str] = []
    exclude_suffixes: list[str] = []


class V2rayDomainOption(BaseModel):
    attrs: V2rayDomainAttrs | None = None
    exclude_includes: list[str] | None = None


class GeoIPOption(BaseModel):
    country_code: str | None = None


class Option(BaseModel):
    """Unified configuration option container"""

    serialization: SerializationOption = SerializationOption()
    processing: ProcessingOption = ProcessingOption()
    v2ray_domain: V2rayDomainOption = V2rayDomainOption(
        attrs=V2rayDomainAttrs(), exclude_includes=[]
    )
    geo_ip: GeoIPOption = GeoIPOption()

    @field_validator("v2ray_domain", mode="before")
    def set_default_v2ray_domain_option(cls, v: V2rayDomainOption) -> V2rayDomainOption:
        """Set default values for V2rayDomainOption fields if they are None."""
        if v.attrs is None:
            v.attrs = V2rayDomainAttrs()
        if v.exclude_includes is None:
            v.exclude_includes = []
        return v
