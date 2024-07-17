from time import sleep
from pathlib import Path

from httpx import Client, HTTPTransport
from loguru import logger
from pydantic import HttpUrl

from cache import Cache


class Fetcher:
    def __init__(self) -> None:
        self.retries = 5
        self.client = Client(
            http2=True, timeout=10, transport=HTTPTransport(retries=self.retries)
        )
        self.cache = Cache(path="fetcher")

    def get(self, path: HttpUrl | Path) -> str:
        logger.info(path)
        if isinstance(path, Path):
            with path.open() as f:
                return f.read()
        url = path.unicode_string()
        if cache := self.cache.get(url):
            return cache
        err = None
        for _ in range(self.retries):
            try:
                res = self.client.get(url)
                if res.is_success:
                    self.cache.set(url, res.text)
                    return res.text
            except Exception as e:
                err = e
                sleep(2)
        raise Exception(err)


fetcher = Fetcher()
