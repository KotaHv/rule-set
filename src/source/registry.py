from typing import Iterator
from model import SourceModel
from .dep_resolver import DependencyResolver


class SourceRegistry:
    def __init__(self, sources: list[SourceModel]):
        resolver = DependencyResolver(sources)
        self._sources = resolver.resolve_order()

    def __iter__(self) -> Iterator[SourceModel]:
        return iter(self._sources)

    def __len__(self) -> int:
        return len(self._sources)
