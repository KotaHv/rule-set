from collections import defaultdict
import ipaddress
from pathlib import Path
from typing import Annotated, Any, Self
from enum import Enum

from pydantic import (
    BaseModel,
    HttpUrl,
    BeforeValidator,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    field_validator,
    model_validator,
)
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue
from loguru import logger


from anytree import Node

from serialize.logical import surge_logical_serialize
from deserialize.logical import deserialize as logical_deserialize
from utils import is_eTLD


class SerializeFormat(str, Enum):
    Surge = "Surge"
    Loon = "Loon"
    Egern = "Egern"
    Clash = "Clash"
    Sing_Box = "sing-box"
    GeoIP = "GeoIP"


SerializeFormats = Annotated[
    list[SerializeFormat],
    BeforeValidator(lambda x: [x] if isinstance(x, SerializeFormat) else x),
]


class ResourceFormat(str, Enum):
    RuleSet = "RULE-SET"
    DomainSet = "DOMAIN-SET"
    MaxMindDB = "MaxMind DB"
    V2RayDomain = "V2RAY-DOMAIN"


class SourceResource(BaseModel):
    path: HttpUrl | Path
    format: ResourceFormat = ResourceFormat.RuleSet

    @property
    def name(self) -> str:
        if self.is_dir():
            name = self.path
        elif self.is_path():
            name = self.path.name
        else:
            name = self.path.unicode_string().split("/")[-1]
        return str(name)

    @model_validator(mode="before")
    @classmethod
    def validate_input(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"path": data}
        if isinstance(data, tuple) and len(data) == 2:
            return {"path": data[0], "format": data[1]}
        return data

    def is_path(self) -> bool:
        return isinstance(self.path, Path)

    def is_dir(self) -> bool:
        try:
            return self.path.is_dir()
        except AttributeError:
            return False

    def is_file(self) -> bool:
        try:
            return self.path.is_file()
        except AttributeError:
            return False


SourceResources = Annotated[
    list[SourceResource],
    BeforeValidator(lambda x: [x] if not isinstance(x, list) else x),
]


class V2rayAttrMode(str, Enum):
    ALL = "ALL"
    NO_ATTR = "NO_ATTR"
    ATTRS = "ATTRS"


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
        return False

    def __repr__(self) -> str:
        if self.mode == V2rayAttrMode.ATTRS:
            return f"ATTRS<{'|'.join(self.attrs)}>"
        return self.mode.value

    def __str__(self) -> str:
        return self.__repr__()


class Option(BaseModel):
    no_resolve: bool = True
    clash_optimize: bool = True
    geo_ip_country_code: str | None = None
    exclude_keywords: list[str] = []
    exclude_suffixes: list[str] = []
    exclude_rule_types: list[str] = []
    optimize_domains: bool = False
    exclude_optimized_domains: list[str] = []
    optimize_domains_by_keyword: bool = False
    v2ray_domain_attrs: V2rayDomainAttr = V2rayDomainAttr.ALL()


class SourceModel(BaseModel):
    resources: SourceResources
    target_path: Path | None = None
    exclude: SerializeFormats = []
    include: SerializeFormats | None = None
    option: Option = Option()

    @model_validator(mode="after")
    def check_target_path(self) -> Self:
        if len(self.resources) > 1:
            if self.target_path is None:
                raise ValueError(
                    "target_path cannot be empty when there are multiple resources"
                )
        if self.target_path is None:
            self.target_path = Path(self.resources[0].name)
        return self

    def __repr__(self) -> str:
        if len(self.resources) == 1:
            resource = self.resources[0]
            if resource.is_dir():
                return f'{self.target_path}: "{list(resource.path.iterdir())}"'
            return f'{self.target_path}: "{resource}"'
        return f"{self.target_path}: {self.resources}"

    def __str__(self) -> str:
        return self.__repr__()


class AnyTreeNodePydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        def validate_from_str(value: str) -> Node:
            node = logical_deserialize(value)
            if node is None:
                raise ValueError("Invalid rule format")
            return node

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(Node),
                    from_str_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: surge_logical_serialize(root_node=instance)
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.dict_schema())


AnyTreeNode = Annotated[Node, AnyTreeNodePydanticAnnotation]


class RuleModel(BaseModel):
    domain: set[str] | list[str] = set()
    domain_suffix: set[str] | list[str] = set()
    domain_keyword: set[str] | list[str] = set()
    domain_wildcard: set[str] | list[str] = set()
    ip_cidr: set[str] | list[str] = set()
    ip_cidr6: set[str] | list[str] = set()
    ip_asn: set[str] | list[str] = set()
    logical: list[AnyTreeNode] = []
    process: set[str] | list[str] = set()
    ua: set[str] | list[str] = set()

    def merge_with(self, other: "RuleModel") -> None:
        self.domain.update(other.domain)
        self.domain_suffix.update(other.domain_suffix)
        self.domain_keyword.update(other.domain_keyword)
        self.domain_wildcard.update(other.domain_wildcard)
        self.ip_cidr.update(other.ip_cidr)
        self.ip_cidr6.update(other.ip_cidr6)
        self.ip_asn.update(other.ip_asn)
        if other.logical:
            node_list = [
                surge_logical_serialize(root_node=node) for node in self.logical
            ]
            for node in other.logical:
                if surge_logical_serialize(root_node=node) in node_list:
                    continue
                self.logical.append(node)
        self.process.update(other.process)
        self.ua.update(other.ua)

    def sort(self):
        for key in self.model_fields.keys():
            value = getattr(self, key)
            if key == "ip_cidr":
                value = sorted(
                    value,
                    key=lambda x: ipaddress.IPv4Network(x).network_address,
                )
            elif key == "ip_cidr6":
                value = sorted(
                    value,
                    key=lambda x: ipaddress.IPv6Network(x).network_address,
                )
            elif key == "ip_asn":
                value = sorted(
                    value,
                    key=lambda x: int(x),
                )
            elif key == "logical":
                value = sorted(
                    value, key=lambda x: surge_logical_serialize(root_node=x)
                )
            else:
                value = sorted(value)
            setattr(self, key, value)

    def _filter_domain(self, domain: str):
        domain_parts = domain.split(".")
        suffixes_to_check = [
            ".".join(domain_parts[i:]) for i in range(len(domain_parts))
        ]
        for suffix in suffixes_to_check:
            if suffix in self.domain_suffix:
                logger.error(f"DOMAIN,{domain} -> DOMAIN-SUFFIX,{suffix}")
                return False
        return True

    def _filter_domain_suffix(self, domain_suffix: str):
        domain_suffix_parts = domain_suffix.split(".")
        suffixes_to_check = [
            ".".join(domain_suffix_parts[i:])
            for i in range(1, len(domain_suffix_parts))
        ]
        for suffix in suffixes_to_check:
            if suffix in self.domain_suffix:
                logger.error(f"DOMAIN-SUFFIX,{domain_suffix} -> DOMAIN-SUFFIX,{suffix}")
                return False
        return True

    def _filter_domain_suffix_by_keyword(self, domain_suffix: str):
        for keyword in self.domain_keyword:
            if keyword in domain_suffix:
                logger.error(
                    f"DOMAIN-SUFFIX,{domain_suffix} -> DOMAIN-KEYWORD,{keyword}"
                )
                return False
        return True

    def _optimize_domains(self, exclude_optimized_domains: list[str] = []):
        for domain in self.domain:
            domain_parts = domain.split(".")
            for index in range(len(domain_parts) - 1, -1, -1):
                current_suffix = ".".join(domain_parts[index:])
                if is_eTLD(current_suffix):
                    continue
                logger.error(f"DOMAIN,{domain} -> DOMAIN-SUFFIX,{current_suffix}")
                self.domain_suffix.add(current_suffix)
                break
        self.domain.clear()
        domain_suffix_count = defaultdict(int)
        for domain_suffix in self.domain_suffix:
            domain_suffix_parts = domain_suffix.split(".")
            if len(domain_suffix) <= 2:
                continue
            for index in range(len(domain_suffix_parts) - 2, 0, -1):
                current_suffix = ".".join(domain_suffix_parts[index:])
                if is_eTLD(current_suffix):
                    continue
                if current_suffix in self.domain_suffix:
                    break
                domain_suffix_count[current_suffix] += 1
        for domain_suffix, count in domain_suffix_count.items():
            if count > 1 and domain_suffix not in exclude_optimized_domains:
                logger.error(domain_suffix)
                if isinstance(self.domain_suffix, set):
                    self.domain_suffix.add(domain_suffix)
                elif isinstance(self.domain_suffix, list):
                    self.domain_suffix.append(domain_suffix)

    def _filter_domain_keyword(self, candidate_keyword: str):
        for current_keyword in self.domain_keyword:
            if (
                current_keyword != candidate_keyword
                and current_keyword in candidate_keyword
            ):
                logger.error(
                    f"DOMAIN-KEYWORD,{candidate_keyword} -> DOMAIN-KEYWORD,{current_keyword}"
                )
                return False
        return True

    def filter(self, option: Option):
        self.domain = set(filter(self._filter_domain, self.domain))
        self.domain_keyword = set(
            filter(self._filter_domain_keyword, self.domain_keyword)
        )
        if option.optimize_domains_by_keyword:
            self.domain_suffix = set(
                filter(self._filter_domain_suffix_by_keyword, self.domain_suffix)
            )
        if option.optimize_domains:
            self._optimize_domains(option.exclude_optimized_domains)
        self.domain_suffix = set(filter(self._filter_domain_suffix, self.domain_suffix))

    def has_only_ip_cidr_rules(self, ignore_types: list = []) -> bool:
        return self._has_only_rules_of_type(["ip_cidr", "ip_cidr6"], ignore_types)

    def has_only_domain_rules(self, ignore_types: list = []) -> bool:
        return self._has_only_rules_of_type(["domain", "domain_suffix"], ignore_types)

    def _has_only_rules_of_type(
        self, allowed_types: list, ignore_types: list = []
    ) -> bool:
        rule_types = list(self.model_fields.keys())
        ignore_types = set(allowed_types + ignore_types)
        for rule_type in ignore_types:
            rule_types.remove(rule_type)
        for rule_type in rule_types:
            if getattr(self, rule_type):
                return False
        return any(getattr(self, rule_type) for rule_type in allowed_types)

    def count_rules(self, ignore_types: list = []) -> int:
        count = 0
        rule_types = list(self.model_fields.keys())
        for rule_type in ignore_types:
            rule_types.remove(rule_type)
        for rule_type in rule_types:
            count += len(getattr(self, rule_type))
        return count
