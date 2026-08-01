import shutil

from loguru import logger

from .cache import Cache
from .config import settings
from .metadata import MetadataStore
from .processors import ResourceProcessor, SourceProcessor
from .sources import SOURCES


def main():
    try:
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
        for source in SOURCES:
            source_processor.process(source)
    except Exception as e:
        logger.exception(e)
        raise
