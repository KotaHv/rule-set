from pathlib import Path
from time import sleep

from httpx import Client, ConnectError, ConnectTimeout, HTTPTransport, Response
from loguru import logger
from pydantic import HttpUrl

from .cache import Cache
from .config import settings
from .errors import FetchError


class Fetcher:
    def __init__(self) -> None:
        self.max_retries = settings.http_max_retries
        self.http_client = Client(
            http2=True,
            timeout=settings.http_timeout,
            transport=HTTPTransport(
                retries=self.max_retries, verify=settings.http_verify_ssl
            ),
            follow_redirects=True,
        )
        self.cache = Cache(path="fetcher")

    def close(self) -> None:
        self.http_client.close()

    def _fetch(self, url: str) -> Response:
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.http_client.get(url).raise_for_status()
                return response
            except (ConnectError, ConnectTimeout) as e:
                # HTTPTransport already retried connection failures internally.
                raise FetchError(f"Failed to fetch URL: {e}") from e
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    sleep(2**attempt)
        raise FetchError(
            f"Failed to fetch URL after {self.max_retries} retries: {last_exception}"
        ) from last_exception

    def get_content(self, path: HttpUrl | Path) -> str:
        logger.info(f"Fetching content from: {path}")
        if isinstance(path, Path):
            with path.open() as file:
                return file.read()
        url = path.unicode_string()
        if cached_content := self.cache.retrieve(url):
            return cached_content
        response = self._fetch(url)
        content = response.text
        self.cache.store(url, content)
        return content

    def download_file(self, url: HttpUrl) -> Path:
        logger.info(f"Downloading file from: {url}")
        url = url.unicode_string()
        filepath = self.cache.get_file_path(url)
        if filepath.exists():
            return filepath
        response = self._fetch(url)
        filepath = self.cache.store(url, response.content)
        return filepath


fetcher = Fetcher()
