import shutil
import sys

from loguru import logger

from .cache import Cache
from .config import settings
from .fetcher import fetcher
from .metadata import MetadataStore
from .processors import ResourceProcessor, SourceProcessor
from .sources import SourceRegistry, sources


def main():
    logger.remove()
    _ = logger.add(sys.stderr, level=settings.log_level)

    metadata_store = None
    try:
        source_registry = SourceRegistry(sources)
        legacy_metadata_path = settings.metadata_path.with_suffix(".json")
        if not settings.metadata_path.exists() and not legacy_metadata_path.exists():
            shutil.rmtree(settings.build_dir, ignore_errors=True)
        settings.build_dir.mkdir(parents=True, exist_ok=True)
        settings.cache_dir.mkdir(parents=True, exist_ok=True)
        metadata_store = MetadataStore()
        resource_processor = ResourceProcessor(Cache(path="resource"))
        source_processor = SourceProcessor(
            cache=Cache(path="source"),
            resource_processor=resource_processor,
            metadata_store=metadata_store,
        )
        for source in source_registry:
            source_processor.build(source)
    except Exception as e:
        logger.exception(e)
        raise
    finally:
        if metadata_store is not None:
            metadata_store.close()
        fetcher.close()
