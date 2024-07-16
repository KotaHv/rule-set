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
            if isinstance(source.resource, Path):
                if source.resource.is_dir():
                    filepaths = [filepath for filepath in source.resource.iterdir()]
                else:
                    filepaths = [source.resource]
                for filepath in filepaths:
                    with filepath.open() as f:
                        parser = Parser(f.read())
                        parser.parse()
                        result = parser.result
                    rules.merge_with(result)
                    file_info = source.model_copy(
                        update={
                            "resource": filepath,
                            "target_name": str(filepath.parent / filepath.stem),
                        }
                    )
                    Generator(info=file_info, rules=rules).generate()
            else:
                for resource in source.resource:
                    if result := cache.get(resource):
                        result = RuleModel.model_validate_json(result)
                    else:
                        data = fetcher.get(resource)
                        parser = Parser(data)
                        parser.parse()
                        result = parser.result
                        cache.set(resource, result.model_dump_json())
                    rules.merge_with(result)
                Generator(info=source, rules=rules).generate()
    except Exception as e:
        logger.exception(e)
        Path(".failure").touch()


if __name__ == "__main__":
    main()
