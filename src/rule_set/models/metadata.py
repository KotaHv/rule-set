from pathlib import Path

from pydantic import BaseModel


class MetadataRecord(BaseModel):
    path: Path
    timestamp: float
