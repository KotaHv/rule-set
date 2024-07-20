import ipaddress
from pathlib import Path
from typing import List, Annotated, Set, Any, Self
from enum import Enum

from pydantic import (
    BaseModel,
    HttpUrl,
    BeforeValidator,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    model_validator,
)
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue


from anytree import Node

from serialize.logical import surge_logical_serialize
from deserialize.logical import deserialize as logical_deserialize


class SerializeFormat(str, Enum):
    Surge = "Surge"
    Loon = "Loon"
    Egern = "Egern"
    Clash = "Clash"
    Sing_Box = "sing-box"
    GeoIP = "GeoIP"


SerializeFormats = Annotated[
    List[SerializeFormat],
    BeforeValidator(lambda x: [x] if isinstance(x, SerializeFormat) else x),
]


class ResourceFormat(str, Enum):
    RuleSet = "RULE-SET"
    DomainSet = "DOMAIN-SET"
    MaxMindDB = "MaxMind DB"


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


class SerializeOption(BaseModel):
    no_resolve: bool = True
    clash_optimize: bool = True
    geo_ip_country_code: str | None = None


class SourceModel(BaseModel):
    resources: Annotated[
        List[SourceResource],
        BeforeValidator(lambda x: [x] if not isinstance(x, list) else x),
    ]
    target_path: Path | None = None
    exclude: SerializeFormats = []
    include: SerializeFormats | None = None
    option: SerializeOption = SerializeOption()

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
    domain: Set[str] | List[str] = set()
    domain_suffix: Set[str] | List[str] = set()
    domain_keyword: Set[str] | List[str] = set()
    domain_wildcard: Set[str] | List[str] = set()
    ip_cidr: Set[str] | List[str] = set()
    ip_cidr6: Set[str] | List[str] = set()
    ip_asn: Set[str] | List[str] = set()
    logical: List[AnyTreeNode] = []
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
