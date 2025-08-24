from pathlib import Path

from loguru import logger

from source import SOURCES
from fetcher import fetcher
from model import (
    RuleModel,
    SourceModel,
    SerializeFormat,
    Option,
    V2rayDomainResult,
    BaseResource,
    RuleSetResource,
    DomainSetResource,
    V2rayDomainResource,
    MaxMindDBResource,
    SourceReference,
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
resource_cache = Cache(path="resource")
source_cache = Cache(path="source")


def deserialize_data(
    data: str | list | Path, resource: BaseResource, option: Option
) -> RuleModel | V2rayDomainResult:
    if isinstance(resource, RuleSetResource):
        de = RuleSetDeserialize(
            data,
            exclude_keywords=option.exclude_keywords,
            exclude_suffixes=option.exclude_suffixes,
        )
        return de.deserialize()
    elif isinstance(resource, DomainSetResource):
        de = DomainSetDeserialize(
            data,
            exclude_keywords=option.exclude_keywords,
            exclude_suffixes=option.exclude_suffixes,
        )
        return de.deserialize()
    elif isinstance(resource, MaxMindDBResource):
        return mmdb.deserialize(data, country_code=option.geo_ip_country_code)
    elif isinstance(resource, V2rayDomainResource):
        return v2ray_domain.deserialize(data, option.v2ray_domain_attrs)
    raise Exception(f"Unknown resource type: {type(resource)}")


def pre_process_sources() -> list[SourceModel]:
    sources = []
    for source in SOURCES:
        if source.name.is_dir():
            for resource in source.resources:
                if isinstance(resource, BaseResource):
                    stem = (
                        resource.source.stem
                        if isinstance(resource.source, Path)
                        else resource.source.unicode_string().split("/")[-1]
                    )
                else:
                    stem = resource.target
                sources.append(
                    source.model_copy(
                        update={
                            "resources": [resource],
                            "name": source.name / stem,
                        }
                    )
                )
        else:
            sources.append(source)
    return sources


def process_sources(sources: list[SourceModel]):
    for source in sources:
        if cached_result := source_cache.retrieve(source.name):
            aggregated_rules = RuleModel.model_validate_json(cached_result, strict=True)
        else:
            aggregated_rules = process_source(source)

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
            writer_cls(data=serialized_data, target_path=source.name).write()


def process_source(source: SourceModel) -> RuleModel:
    aggregated_rules = RuleModel()

    for resource in source.resources:
        if isinstance(resource, SourceReference):
            referenced_target = resource.target
            aggregated_rules.merge_with(
                RuleModel.model_validate_json(source_cache.retrieve(referenced_target))
            )
        else:
            aggregated_rules.merge_with(process_resource(resource, source.option))

    for rule_types in source.option.exclude_rule_types:
        setattr(aggregated_rules, rule_types, set())
    aggregated_rules.filter(source.option)
    aggregated_rules.sort()
    source_cache.store(source.name, aggregated_rules.model_dump_json())
    return aggregated_rules


def process_resource(resource: BaseResource, source_option: Option) -> RuleModel:
    aggregated_rules = RuleModel()
    paths = [resource.source]

    for path in paths:
        cache_key = str(path)
        if isinstance(resource, V2rayDomainResource):
            cache_key += f"::attrs={source_option.v2ray_domain_attrs}"

        if cached_result := resource_cache.retrieve(cache_key):
            if isinstance(resource, V2rayDomainResource):
                deserialized_rules = V2rayDomainResult.model_validate_json(
                    cached_result
                )
            else:
                deserialized_rules = RuleModel.model_validate_json(cached_result)
        else:
            if isinstance(resource, MaxMindDBResource):
                data = fetcher.download_file(path)
            else:
                data = fetcher.get_content(path)
            deserialized_rules = deserialize_data(data, resource, source_option)
            resource_cache.store(cache_key, deserialized_rules.model_dump_json())

        if isinstance(deserialized_rules, V2rayDomainResult):
            for include in deserialized_rules.includes:
                if include in source_option.v2ray_domain_exclude_includes:
                    continue
                paths.append(build_v2ray_include_url(path, include))
            deserialized_rules = deserialized_rules.rules

        aggregated_rules.merge_with(deserialized_rules)
    return aggregated_rules


def main():
    try:
        sources = pre_process_sources()
        process_sources(sources)
    except Exception as e:
        logger.exception(e)
        Path(".failure").touch()
