from pathlib import Path

from loguru import logger

from .cache import Cache
from .fetcher import fetcher
from .file_writers import (
    ClashFileWriter,
    EgernFileWriter,
    GeoIPFileWriter,
    LoonFileWriter,
    SingBoxFileWriter,
    SurgeFileWriter,
)
from .file_writers.base import BaseFileWriter
from .models import (
    BaseResource,
    DomainSetResource,
    MaxMindDBResource,
    Option,
    RuleModel,
    RuleSetResource,
    SerializeFormat,
    SourceModel,
    SourceReference,
    V2rayDomainOption,
    V2rayDomainResource,
    V2rayDomainResult,
)
from .parsers import mmdb, v2ray_domain
from .parsers.surge import DomainSetParser, RuleSetParser
from .serializers.clients import (
    ClashSerializer,
    EgernSerializer,
    GeoIPSerializer,
    LoonSerializer,
    SingBoxSerializer,
    SurgeSerializer,
)
from .serializers.clients.base import BaseSerializer
from .sources import SOURCES
from .utils import build_v2ray_include_url

client_serializers_writers: dict[
    SerializeFormat, tuple[BaseSerializer, BaseFileWriter]
] = {
    SerializeFormat.Surge: (SurgeSerializer, SurgeFileWriter),
    SerializeFormat.Loon: (LoonSerializer, LoonFileWriter),
    SerializeFormat.Clash: (ClashSerializer, ClashFileWriter),
    SerializeFormat.Egern: (EgernSerializer, EgernFileWriter),
    SerializeFormat.Sing_Box: (SingBoxSerializer, SingBoxFileWriter),
    SerializeFormat.GeoIP: (GeoIPSerializer, GeoIPFileWriter),
}
resource_cache = Cache(path="resource")
source_cache = Cache(path="source")


def parse_data(
    data: str | list | Path, resource: BaseResource, option: Option | V2rayDomainOption
) -> RuleModel | V2rayDomainResult:
    if isinstance(resource, RuleSetResource):
        de = RuleSetParser(data)
        return de.parse()
    elif isinstance(resource, DomainSetResource):
        de = DomainSetParser(data)
        return de.parse()
    elif isinstance(resource, MaxMindDBResource):
        return mmdb.parse(data, country_code=option.geo_ip.country_code)
    elif isinstance(resource, V2rayDomainResource):
        return v2ray_domain.parse(data, option)
    raise Exception(f"Unknown resource type: {type(resource)}")


def process_sources(sources: list[SourceModel]):
    for source in sources:
        if cached_result := source_cache.retrieve(source.name):
            aggregated_rules = RuleModel.model_validate_json(cached_result, strict=True)
        else:
            aggregated_rules = process_source(source)
        serializable_rules = aggregated_rules.to_serializable_rule_model()

        target_clients = (
            source.include
            if source.include
            else filter(
                lambda x: x not in source.exclude
                and not (
                    source.option.geo_ip.country_code is None
                    and x == SerializeFormat.GeoIP
                ),
                client_serializers_writers.keys(),
            )
        )
        for client in target_clients:
            serializer_cls, writer_cls = client_serializers_writers[client]
            serialized_data = serializer_cls(
                rules=serializable_rules, option=source.option
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
            cache_key += f"::attrs={resource.option.attrs}"

        if cached_result := resource_cache.retrieve(cache_key):
            if isinstance(resource, V2rayDomainResource):
                parsed_rules = V2rayDomainResult.model_validate_json(cached_result)
            else:
                parsed_rules = RuleModel.model_validate_json(cached_result)
        else:
            if isinstance(resource, MaxMindDBResource):
                data = fetcher.download_file(path)
            else:
                data = fetcher.get_content(path)
            if isinstance(resource, V2rayDomainResource):
                parsed_rules = parse_data(data, resource, resource.option)
            else:
                parsed_rules = parse_data(data, resource, source_option)
            resource_cache.store(cache_key, parsed_rules.model_dump_json())

        if isinstance(parsed_rules, V2rayDomainResult):
            for include in parsed_rules.includes:
                paths.append(build_v2ray_include_url(path, include))
            parsed_rules = parsed_rules.rules

        aggregated_rules.merge_with(parsed_rules)
    return aggregated_rules


def main():
    try:
        process_sources(SOURCES)
    except Exception as e:
        logger.exception(e)
        Path(".failure").touch()
