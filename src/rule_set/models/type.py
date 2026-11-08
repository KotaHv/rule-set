from pathlib import Path
from typing import Annotated

from pydantic import (
    BeforeValidator,
    Field,
    HttpUrl,
)

from .enum import SerializeFormat

# Try HttpUrl before Path: Pydantic's smart union otherwise parses URL
# strings from cache as local paths.
type Source = Annotated[HttpUrl | Path, Field(union_mode="left_to_right")]


def _ensure_list(value: object) -> object:
    if isinstance(value, SerializeFormat):
        return [value]
    return value


# Type aliases
SerializeFormats = Annotated[
    list[SerializeFormat],
    BeforeValidator(_ensure_list),
]
