from pathlib import Path
from typing import List

from loguru import logger

from source import SOURCES
from fetcher import fetcher
from model import RuleModel, SourceModel, ResourceFormat
from generator import Generator
from cache import Cache
from deserialize import SurgeDomainSetDeserialize, SurgeRuleSetDeserialize


def deserialize(data: str | list, format: ResourceFormat) -> RuleModel:
    if format == ResourceFormat.RuleSet:
        de = SurgeRuleSetDeserialize(data)
        return de.deserialize()
    elif format == ResourceFormat.DomainSet:
        de = SurgeDomainSetDeserialize(data)
        return de.deserialize()
    raise Exception(f"unknown format: {format}")


def process_sources() -> List[SourceModel]:
    sources = []
    for source in SOURCES:
        resources = []
        for resource in source.resources:
            if resource.is_dir():
                resources.extend(
                    [
                        resource.model_copy(update={"path": filepath})
                        for filepath in resource.path.iterdir()
                    ]
                )
            else:
                resources.append(resource)

        if source.target_name.is_dir():
            for resource in resources:
                logger.debug(resource)
                sources.append(
                    source.model_copy(
                        update={
                            "resources": [resource],
                            "target_name": source.target_name / resource.path.stem,
                        }
                    )
                )
        else:
            sources.append(source.model_copy(update={"resources": resources}))
    return sources


def _main():
    cache = Cache(path="parser")
    sources = process_sources()
    for source in sources:
        rules = RuleModel()
        for resource in source.resources:
            if result := cache.get(resource.path):
                result = RuleModel.model_validate_json(result)
            else:
                data = fetcher.get(resource.path)
                result = deserialize(data, resource.format)
                cache.set(resource.path, result.model_dump_json())
            rules.merge_with(result)
        Generator(info=source, rules=rules).generate()


def main():
    try:
        _main()
    except Exception as e:
        logger.exception(e)
        Path(".failure").touch()


if __name__ == "__main__":
    main()
