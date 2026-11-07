from pathlib import Path
from typing import Annotated

from pydantic import (
    BeforeValidator,
    HttpUrl,
)

from .enum import SerializeFormat

# New resource type system - using Python 3.13 syntax
type Source = HttpUrl | Path


def _ensure_list(value: object) -> object:
    if isinstance(value, SerializeFormat):
        return [value]
    return value


# Type aliases
SerializeFormats = Annotated[
    list[SerializeFormat],
    BeforeValidator(_ensure_list),
]
