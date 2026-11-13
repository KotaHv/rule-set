import shutil

from .cache import Cache
from .config import settings
from .metadata import MetadataStore
from .prefetch import prefetch_resources
from .processors import ResourceProcessor, SourceProcessor
from .sources import SourceRegistry


class BuildPipeline:
    """Run the cache prefetch and source build stages."""

    def __init__(self, source_registry: SourceRegistry) -> None:
        self.source_registry: SourceRegistry = source_registry

    def run(self) -> None:
        self._prepare_build()

        resource_processor = ResourceProcessor(Cache(path="resource"))
        prefetch_resources(self.source_registry, resource_processor)

        with MetadataStore() as metadata_store:
            source_processor = SourceProcessor(
                cache=Cache(path="source"),
                resource_processor=resource_processor,
                metadata_store=metadata_store,
            )
            for source in self.source_registry:
                source_processor.build(source)

    def _prepare_build(self) -> None:
        legacy_metadata_path = settings.metadata_path.with_suffix(".json")
        if not settings.metadata_path.exists() and not legacy_metadata_path.exists():
            shutil.rmtree(settings.build_dir, ignore_errors=True)
        settings.build_dir.mkdir(parents=True, exist_ok=True)
        settings.cache_dir.mkdir(parents=True, exist_ok=True)
