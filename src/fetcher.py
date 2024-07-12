from time import sleep

from httpx import Client, HTTPTransport
from loguru import logger

from model import Url


class Fetcher:
    def __init__(self) -> None:
        self.retries = 5
        self.client = Client(
            http2=True, timeout=10, transport=HTTPTransport(retries=self.retries)
        )

    def get(self, url: Url) -> str:
        logger.info(url)
        err = None
        for _ in range(self.retries):
            try:
                res = self.client.get(url)
                if res.is_success:
                    return res.text
            except Exception as e:
                err = e
                sleep(2)
        raise Exception(err)


fetcher = Fetcher()
