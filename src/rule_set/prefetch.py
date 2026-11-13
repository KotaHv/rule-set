from collections.abc import Iterable
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from threading import Lock

from loguru import logger
from pydantic import HttpUrl

from .config import settings
from .fetcher import fetcher
from .models import (
    ContentResource,
    SourceModel,
    V2rayDomainResource,
    V2rayDomainResult,
)
from .processors.resource import ResourceProcessor


def _download(url: HttpUrl) -> bool:
    try:
        _ = fetcher.download_file(url)
    except Exception as error:
        logger.warning(f"Failed to prefetch '{url}': {error}")
        return False
    return True


def prefetch_resources(
    sources: Iterable[SourceModel], processor: ResourceProcessor
) -> None:
    """Warm the caches with HTTP resources and any V2Ray include chains."""
    normal_urls: set[HttpUrl] = set()
    v2ray_resources: list[V2rayDomainResource] = []
    for source in sources:
        for resource in source.resources:
            if not isinstance(resource, ContentResource):
                continue
            url = resource.source
            if not isinstance(url, HttpUrl):
                continue
            if isinstance(resource, V2rayDomainResource):
                v2ray_resources.append(resource)
            else:
                normal_urls.add(url)

    if not normal_urls and not v2ray_resources:
        return

    count = len(normal_urls) + len(v2ray_resources)
    logger.info(
        f"Prefetching {count} resources with {settings.http_concurrency} workers"
    )
    with ThreadPoolExecutor(max_workers=settings.http_concurrency) as executor:
        for url in normal_urls:
            _ = executor.submit(_download, url)

        locks_guard = Lock()
        locks: dict[str, Lock] = {}

        def lock_for(key: str) -> Lock:
            with locks_guard:
                return locks.setdefault(key, Lock())

        def prefetch_v2ray(resource: V2rayDomainResource) -> list[V2rayDomainResource]:
            url = resource.source
            if not isinstance(url, HttpUrl):
                return []
            with lock_for(url.unicode_string()):
                if not _download(url):
                    return []
            try:
                result = processor.load(resource)
            except Exception as error:
                logger.warning(f"Failed to prefetch '{url}': {error}")
                return []
            return result.resources if isinstance(result, V2rayDomainResult) else []

        scheduled: set[str] = set()
        futures: set[Future[list[V2rayDomainResource]]] = set()

        def schedule(resource: V2rayDomainResource) -> None:
            key = resource.cache_key()
            if key in scheduled:
                return
            scheduled.add(key)
            futures.add(executor.submit(prefetch_v2ray, resource))

        for resource in v2ray_resources:
            schedule(resource)

        while futures:
            done, futures = wait(futures, return_when=FIRST_COMPLETED)
            for future in done:
                for include in future.result():
                    schedule(include)
