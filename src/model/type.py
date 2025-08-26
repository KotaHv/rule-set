from pathlib import Path
from typing import Annotated, Any
from pydantic import (
    HttpUrl,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    BeforeValidator,
)
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue

from anytree import Node
from serialize.logical import surge_logical_serialize
from deserialize.logical import deserialize as logical_deserialize

from .enum import SerializeFormat


# New resource type system - using Python 3.13 syntax
type Source = HttpUrl | Path


# Type aliases
SerializeFormats = Annotated[
    list[SerializeFormat],
    BeforeValidator(lambda x: [x] if isinstance(x, SerializeFormat) else x),
]


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
