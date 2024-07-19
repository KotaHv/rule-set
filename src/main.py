from pathlib import Path
from typing import Dict, List, Tuple

from loguru import logger

from source import SOURCES
from fetcher import fetcher
from model import RuleModel, SourceModel, ResourceFormat, ClientEnum
from cache import Cache
from deserialize.surge import DomainSetDeserialize, RuleSetDeserialize
from serialize.client import (
    SurgeSerialize,
    LoonSerialize,
    ClashSerialize,
    EgernSerialize,
    SingBoxSerialize,
)
from serialize.client.base import BaseSerialize
from file_writer import (
    SurgeFileWriter,
    LoonFileWriter,
    ClashFileWriter,
    EgernFileWriter,
    SingBoxFileWriter,
)
from file_writer.base import BaseFileWriter

client_ser_write: Dict[ClientEnum, Tuple[BaseSerialize, BaseFileWriter]] = {
    ClientEnum.Surge: (SurgeSerialize, SurgeFileWriter),
    ClientEnum.Loon: (LoonSerialize, LoonFileWriter),
    ClientEnum.Clash: (ClashSerialize, ClashFileWriter),
    ClientEnum.Egern: (EgernSerialize, EgernFileWriter),
    ClientEnum.Sing_Box: (SingBoxSerialize, SingBoxFileWriter),
}


def deserialize(data: str | list, format: ResourceFormat) -> RuleModel:
    if format == ResourceFormat.RuleSet:
        de = RuleSetDeserialize(data)
        return de.deserialize()
    elif format == ResourceFormat.DomainSet:
        de = DomainSetDeserialize(data)
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

        if source.target_path.is_dir():
            for resource in resources:
                sources.append(
                    source.model_copy(
                        update={
                            "resources": [resource],
                            "target_path": source.target_path / resource.path.stem,
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
        rules.sort()

        if source.include:
            clients = source.include
        else:
            clients = list(client_ser_write.keys())
            for client in source.exclude:
                clients.remove(client)
        for client in clients:
            ser, write = client_ser_write[client]
            data = ser(rules=rules, option=source.option).serialize()
            write(data=data, target_path=source.target_path).write()


def main():
    try:
        _main()
    except Exception as e:
        logger.exception(e)
        Path(".failure").touch()


if __name__ == "__main__":
    main()
