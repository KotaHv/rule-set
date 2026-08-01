from pathlib import Path

from pydantic import BaseModel


class WriteContext(BaseModel):
    filepath: Path
    timestamp: float
