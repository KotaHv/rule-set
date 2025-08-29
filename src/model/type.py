from pathlib import Path
from typing import Annotated
from pydantic import (
    HttpUrl,
    BeforeValidator,
)


from .enum import SerializeFormat


# New resource type system - using Python 3.13 syntax
type Source = HttpUrl | Path


# Type aliases
SerializeFormats = Annotated[
    list[SerializeFormat],
    BeforeValidator(lambda x: [x] if isinstance(x, SerializeFormat) else x),
]
