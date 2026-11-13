from loguru import logger

from .fetcher import fetcher
from .log import setup_logging
from .pipeline import BuildPipeline
from .sources import SourceRegistry, sources


def main():
    setup_logging()

    try:
        BuildPipeline(SourceRegistry(sources)).run()
    except Exception as e:
        logger.exception(e)
        raise
    finally:
        fetcher.close()
