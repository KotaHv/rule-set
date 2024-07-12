from time import sleep

from httpx import Client, HTTPTransport
from loguru import logger

from model import Url
from cache import Cache


class Fetcher:
    def __init__(self) -> None:
        self.retries = 5
        self.client = Client(
            http2=True, timeout=10, transport=HTTPTransport(retries=self.retries)
        )
        self.cache = Cache(path="fetcher")

    def get(self, url: Url) -> str:
        logger.info(url)
        if cache := self.cache.get(url):
            logger.success(f"{url} hit fetcher cache")
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
