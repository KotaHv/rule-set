from pathlib import Path

from loguru import logger

from source import SOURCES
from fetcher import fetcher
from model import RuleModel
from parser import Parser
from generator import Generator
from cache import Cache


def main():
    try:
        cache = Cache(path="parser")
        for source in SOURCES:
            logger.info(source)
            rules = RuleModel()
            for url in source.urls:
                if result := cache.get(url):
                    result = RuleModel.model_validate_json(result)
                else:
                    data = fetcher.get(url)
                    parser = Parser(data)
                    parser.parse()
                    result = parser.result
                    cache.set(url, result.model_dump_json())
                rules.merge_with(result)
            Generator(info=source, rules=rules).generate()
    except Exception as e:
        logger.exception(e)
        Path(".failure").touch()


if __name__ == "__main__":
    main()
