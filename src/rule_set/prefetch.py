from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor

from loguru import logger
from pydantic import HttpUrl

from .config import settings
from .fetcher import fetcher
from .models import ContentResource, SourceModel


def _prefetch_one(url: HttpUrl) -> None:
    try:
        _ = fetcher.download_file(url)
    except Exception as error:
        logger.warning(f"Failed to prefetch '{url}': {error}")


def prefetch_resources(sources: Iterable[SourceModel]) -> None:
    """Download HTTP resources concurrently so later processing hits the cache."""
    urls = {
        resource.source
        for source in sources
        for resource in source.resources
        if isinstance(resource, ContentResource)
        and isinstance(resource.source, HttpUrl)
    }

    if not urls:
        return

    logger.info(
        f"Prefetching {len(urls)} resources with {settings.http_concurrency} workers"
    )
    with ThreadPoolExecutor(max_workers=settings.http_concurrency) as executor:
        for _ in executor.map(_prefetch_one, urls):
            pass
