from loguru import logger

from .cache import Cache
from .metadata import MetadataStore
from .processors import ResourceProcessor, SourceProcessor
from .sources import SOURCES


def main():
    try:
        metadata_store = MetadataStore()
        resource_processor = ResourceProcessor(Cache(path="resource"))
        source_processor = SourceProcessor(
            cache=Cache(path="source"),
            resource_processor=resource_processor,
            metadata_store=metadata_store,
        )
        for source in SOURCES:
            source_processor.process(source)
        metadata_store.save()
    except Exception as e:
        logger.exception(e)
        raise
