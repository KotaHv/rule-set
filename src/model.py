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

import logic_rule_proc


class ClientEnum(str, Enum):
    Surge = "Surge"
    Loon = "Loon"
    Egern = "Egern"
    Clash = "Clash"
    Sing_Box = "sing-box"


ClientEnums = Annotated[
    List[ClientEnum],
    BeforeValidator(lambda x: [x] if isinstance(x, ClientEnum) else x),
]


class ResourceFormat(str, Enum):
    RuleSet = "RULE-SET"
    DomainSet = "DOMAIN-SET"


class SourceResource(BaseModel):
    path: HttpUrl | Path
    format: ResourceFormat = ResourceFormat.RuleSet

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


class SourceModel(BaseModel):
    resources: Annotated[
        List[SourceResource],
        BeforeValidator(lambda x: [x] if not isinstance(x, list) else x),
    ]
    target_name: Path | None = None
    exclude: ClientEnums = []
    include: ClientEnums | None = None
    no_resolve: bool = True

    @model_validator(mode="after")
    def check_target_name(self) -> Self:
        if len(self.resources) > 1:
            if self.target_name is None:
                raise ValueError(
                    "target_name cannot be empty when there are multiple resources"
                )
        if self.target_name is None:
            resource = self.resources[0]
            if resource.is_path():
                if resource.is_dir():
                    self.target_name = resource.path
                else:
                    self.target_name = resource.path.name
            else:
                self.target_name = resource.path.unicode_string().split("/")[-1]
        return self

    def __repr__(self) -> str:
        if len(self.resources) == 1:
            resource = self.resources[0]
            if resource.is_dir():
                return f'{self.target_name}: "{list(resource.path.iterdir())}"'
            return f'{self.target_name}: "{resource}"'
        return f"{self.target_name}: {self.resources}"

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
            node = logic_rule_proc.deserialize(value)
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
                lambda instance: logic_rule_proc.serialize(node=instance)
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
            node_list = [logic_rule_proc.serialize(node=node) for node in self.logical]
            for node in other.logical:
                if logic_rule_proc.serialize(node=node) in node_list:
                    continue
                self.logical.append(node)
        self.process.update(other.process)
        self.ua.update(other.ua)
