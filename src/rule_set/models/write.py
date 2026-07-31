from pathlib import Path

from pydantic import BaseModel


class WriteContext(BaseModel):
    filepath: Path
    timestamp: float
    generated_paths: list[Path]
