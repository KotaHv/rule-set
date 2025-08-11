from pathlib import Path

from loguru import logger

from source import SOURCES
from fetcher import fetcher
from model import (
    RuleModel,
    SourceModel,
    ResourceFormat,
    SerializeFormat,
    Option,
    V2rayDomainResult,
)
from cache import Cache
from deserialize.surge import DomainSetDeserialize, RuleSetDeserialize
from deserialize import mmdb
from deserialize import v2ray_domain
from serialize.client import (
    SurgeSerialize,
    LoonSerialize,
    ClashSerialize,
    EgernSerialize,
    SingBoxSerialize,
)
from serialize.v2ray_geo_ip import GeoIPSerialize
from serialize.client.base import BaseSerialize
from file_writer import (
    SurgeFileWriter,
    LoonFileWriter,
    ClashFileWriter,
    EgernFileWriter,
    SingBoxFileWriter,
    GeoIPFileWriter,
)
from file_writer.base import BaseFileWriter
from utils import build_v2ray_include_url

client_serializers_writers: dict[
    SerializeFormat, tuple[BaseSerialize, BaseFileWriter]
] = {
    SerializeFormat.Surge: (SurgeSerialize, SurgeFileWriter),
    SerializeFormat.Loon: (LoonSerialize, LoonFileWriter),
    SerializeFormat.Clash: (ClashSerialize, ClashFileWriter),
    SerializeFormat.Egern: (EgernSerialize, EgernFileWriter),
    SerializeFormat.Sing_Box: (SingBoxSerialize, SingBoxFileWriter),
    SerializeFormat.GeoIP: (GeoIPSerialize, GeoIPFileWriter),
}


def deserialize_data(
    data: str | list | Path, format: ResourceFormat, option: Option
) -> RuleModel | V2rayDomainResult:
    if format == ResourceFormat.RuleSet:
        de = RuleSetDeserialize(
            data,
            exclude_keywords=option.exclude_keywords,
            exclude_suffixes=option.exclude_suffixes,
        )
        return de.deserialize()
    elif format == ResourceFormat.DomainSet:
        de = DomainSetDeserialize(
            data,
            exclude_keywords=option.exclude_keywords,
            exclude_suffixes=option.exclude_suffixes,
        )
        return de.deserialize()
    elif format == ResourceFormat.MaxMindDB:
        return mmdb.deserialize(data, country_code=option.geo_ip_country_code)
    elif format == ResourceFormat.V2RayDomain:
        return v2ray_domain.deserialize(data, option.v2ray_domain_attrs)
    raise Exception(f"Unknown format: {format}")


def process_sources() -> list[SourceModel]:
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
        aggregated_rules = RuleModel()
        for resource in source.resources:
            paths = [resource.path]
            for path in paths:
                cache_key = str(path)
                if resource.format == ResourceFormat.V2RayDomain:
                    cache_key += f"::attrs={source.option.v2ray_domain_attrs}"
                if cached_result := cache.retrieve(cache_key):
                    if resource.format == ResourceFormat.V2RayDomain:
                        deserialized_rules = V2rayDomainResult.model_validate_json(
                            cached_result
                        )
                    else:
                        deserialized_rules = RuleModel.model_validate_json(
                            cached_result
                        )
                else:
                    if resource.format == ResourceFormat.MaxMindDB:
                        data = fetcher.download_file(path)
                    else:
                        data = fetcher.get_content(path)
                    deserialized_rules = deserialize_data(
                        data, resource.format, source.option
                    )
                    cache.store(cache_key, deserialized_rules.model_dump_json())
                if isinstance(deserialized_rules, V2rayDomainResult):
                    for include in deserialized_rules.includes:
                        if include in source.option.v2ray_domain_exclude_includes:
                            continue
                        paths.append(build_v2ray_include_url(path, include))
                    aggregated_rules.merge_with(deserialized_rules.rules)
                else:
                    aggregated_rules.merge_with(deserialized_rules)
        for rule_types in source.option.exclude_rule_types:
            setattr(aggregated_rules, rule_types, set())
        aggregated_rules.filter(source.option)
        aggregated_rules.sort()

        target_clients = (
            source.include
            if source.include
            else filter(
                lambda x: x not in source.exclude,
                client_serializers_writers.keys(),
            )
        )
        for client in target_clients:
            serializer_cls, writer_cls = client_serializers_writers[client]
            serialized_data = serializer_cls(
                rules=aggregated_rules, option=source.option
            ).serialize()
            writer_cls(data=serialized_data, target_path=source.target_path).write()


def main():
    try:
        _main()
    except Exception as e:
        logger.exception(e)
        Path(".failure").touch()
