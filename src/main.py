from pathlib import Path

from loguru import logger

from source import SOURCES
from fetcher import fetcher
from model import RuleModel
from parser import Parser
from generator import Generator


def main():
    try:
        for source in SOURCES:
            logger.info(source)
            rules = RuleModel()
            for url in source.urls:
                data = fetcher.get(url)
                parser = Parser(data)
                parser.parse()
                rules.merge_with(parser.result)
            Generator(info=source, rules=rules).generate()
    except Exception as e:
        logger.exception(e)
        Path(".failure").touch()


if __name__ == "__main__":
    main()
