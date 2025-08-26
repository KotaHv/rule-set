from typing import Iterator
from pathlib import Path
from model import SourceModel, BaseResource
from .dep_resolver import DependencyResolver


class SourceRegistry:
    def __init__(self, sources: list[SourceModel]):
        # Preprocess sources to handle split_resources
        expanded_sources = self._preprocess_sources(sources)
        resolver = DependencyResolver(expanded_sources)
        self._sources = resolver.resolve_order()

    def _preprocess_sources(self, sources: list[SourceModel]) -> list[SourceModel]:
        """Preprocess sources to handle split_resources expansion"""
        result = []
        for source in sources:
            if source.split_resources:
                # Create separate SourceModel for each resource
                for resource in source.resources:
                    if isinstance(resource, BaseResource):
                        stem = (
                            resource.source.stem
                            if isinstance(resource.source, Path)
                            else resource.source.unicode_string().split("/")[-1]
                        )
                    else:
                        stem = resource.target
                    result.append(
                        source.model_copy(
                            update={
                                "resources": [resource],
                                "name": source.name / stem,
                                "split_resources": False,  # Prevent recursive splitting
                            }
                        )
                    )
            else:
                result.append(source)
        return result

    def __iter__(self) -> Iterator[SourceModel]:
        return iter(self._sources)

    def __len__(self) -> int:
        return len(self._sources)
