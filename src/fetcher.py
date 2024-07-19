from time import sleep
from pathlib import Path

from httpx import Client, HTTPTransport, Response
from loguru import logger
from pydantic import HttpUrl

from cache import Cache


class Fetcher:
    def __init__(self) -> None:
        self.max_retries = 5
        self.http_client = Client(
            http2=True, timeout=10, transport=HTTPTransport(retries=self.max_retries)
        )
        self.cache = Cache(path="fetcher")

    def _fetch(self, url: str) -> Response:
        last_exception = None
        for _ in range(self.max_retries):
            try:
                response = self.http_client.get(url)
                if response.is_success:
                    return response
            except Exception as e:
                last_exception = e
                sleep(2)
        raise Exception(
            f"Failed to fetch URL after {self.max_retries} retries: {last_exception}"
        )

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
