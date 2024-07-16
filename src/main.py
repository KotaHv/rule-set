from pathlib import Path

from loguru import logger

from source import SOURCES
from fetcher import fetcher
from model import RuleModel, SourceModel
from parser import Parser
from generator import Generator
from cache import Cache


def process_dir(source: SourceModel):
    for filepath in source.resources[0].iterdir():
        with filepath.open() as f:
            data = f.read()
        parser = Parser(data)
        parser.parse()
        file_info = source.model_copy(
            update={
                "resource": [filepath],
                "target_name": source.target_name / filepath.stem,
            }
        )
        Generator(info=file_info, rules=parser.result).generate()


def process_resources(source: SourceModel, cache: Cache):
    rules = RuleModel()
    for resource in source.resources:
        if isinstance(resource, Path):
            if resource.is_dir():
                filepaths = [filepath for filepath in resource.iterdir()]
            else:
                filepaths = [resource]
            for filepath in filepaths:
                with filepath.open() as f:
                    data = f.read()
                parser = Parser(data)
                parser.parse()
                result = parser.result
                rules.merge_with(result)
        else:
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


def main():
    try:
        cache = Cache(path="parser")
        for source in SOURCES:
            logger.info(source)
            if (
                len(source.resources) == 1
                and isinstance(source.resources[0], Path)
                and source.resources[0].is_dir()
            ):
                process_dir(source)
            else:
                process_resources(source, cache)
    except Exception as e:
        logger.exception(e)
        Path(".failure").touch()


if __name__ == "__main__":
    main()
