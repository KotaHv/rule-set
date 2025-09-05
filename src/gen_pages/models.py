"""
Data models for file system tree structure
"""

from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field


class PathInfo(BaseModel):
    """File or directory path information"""

    name: str
    size: int
    mtime: float = 0
    path: Path


class DirNode(BaseModel):
    """Directory node in the tree structure"""

    info: PathInfo
    children: list[Self | "FileNode"] = Field(
        default_factory=list, exclude=True, repr=False
    )
    parent: Self | None = Field(exclude=True, repr=False)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, (DirNode, FileNode)):
            return NotImplemented
        return self.info.name < other.info.name


class FileNode(BaseModel):
    """File node in the tree structure"""

    info: PathInfo
    parent: DirNode = Field(exclude=True, repr=False)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, (DirNode, FileNode)):
            return NotImplemented
        return self.info.name < other.info.name


class PathTree(BaseModel):
    """Complete file system tree structure"""

    root: DirNode
