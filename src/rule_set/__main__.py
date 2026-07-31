from pathlib import Path

from loguru import logger

from .cache import Cache
from .fetcher import fetcher
from .file_writers import (
    ClashClassicalFileWriter,
    ClashDomainFileWriter,
    ClashIpcidrFileWriter,
    EgernFileWriter,
    GeoIPFileWriter,
    LoonFileWriter,
    SingBoxFileWriter,
    SurgeFileWriter,
)
from .file_writers.base import BaseFileWriter
from .metadata import MetadataStore
from .models import (
    ArtifactKind,
    BaseResource,
    DomainSetResource,
    MaxMindDBResource,
    Option,
    RuleModel,
    RuleSetResource,
    SerializeFormat,
    SourceModel,
    SourceReference,
    V2rayDomainAttrs,
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

client_serializers: dict[SerializeFormat, type[BaseSerializer]] = {
    SerializeFormat.Surge: SurgeSerializer,
    SerializeFormat.Loon: LoonSerializer,
    SerializeFormat.Clash: ClashSerializer,
    SerializeFormat.Egern: EgernSerializer,
    SerializeFormat.Sing_Box: SingBoxSerializer,
    SerializeFormat.GeoIP: GeoIPSerializer,
}
writer_registry: dict[tuple[SerializeFormat, ArtifactKind], type[BaseFileWriter]] = {
    (SerializeFormat.Surge, ArtifactKind.DEFAULT): SurgeFileWriter,
    (SerializeFormat.Loon, ArtifactKind.DEFAULT): LoonFileWriter,
    (SerializeFormat.Egern, ArtifactKind.DEFAULT): EgernFileWriter,
    (SerializeFormat.Sing_Box, ArtifactKind.DEFAULT): SingBoxFileWriter,
    (SerializeFormat.GeoIP, ArtifactKind.DEFAULT): GeoIPFileWriter,
    (SerializeFormat.Clash, ArtifactKind.DOMAIN): ClashDomainFileWriter,
    (SerializeFormat.Clash, ArtifactKind.IPCIDR): ClashIpcidrFileWriter,
    (SerializeFormat.Clash, ArtifactKind.CLASSICAL): ClashClassicalFileWriter,
}
resource_cache = Cache(path="resource")
source_cache = Cache(path="source")


def parse_data(
    resource_data: str | list | Path,
    resource: BaseResource,
    option: Option | V2rayDomainOption,
) -> RuleModel | V2rayDomainResult:
    if isinstance(resource, RuleSetResource):
        parser = RuleSetParser(resource_data)
        return parser.parse()
    elif isinstance(resource, DomainSetResource):
        parser = DomainSetParser(resource_data)
        return parser.parse()
    elif isinstance(resource, MaxMindDBResource):
        return mmdb.parse(resource_data, country_code=option.geo_ip.country_code)
    elif isinstance(resource, V2rayDomainResource):
        return v2ray_domain.parse(resource_data, option)
    raise Exception(f"Unknown resource type: {type(resource)}")


def process_sources(sources: list[SourceModel], metadata_store: MetadataStore) -> None:
    for source in sources:
        if cached_result := source_cache.retrieve(source.name):
            aggregated_rules = RuleModel.model_validate_json(cached_result, strict=True)
        else:
            aggregated_rules = process_source(source)
        serializable_rules = aggregated_rules.to_serializable_rule_model()

        selected_serialize_formats = (
            source.include
            if source.include
            else filter(
                lambda serialize_format: (
                    serialize_format not in source.exclude
                    and not (
                        source.option.geo_ip.country_code is None
                        and serialize_format == SerializeFormat.GeoIP
                    )
                ),
                client_serializers.keys(),
            )
        )
        for serialize_format in selected_serialize_formats:
            serializer_cls = client_serializers[serialize_format]
            serializer = serializer_cls(rules=serializable_rules, option=source.option)
            for artifact in serializer.serialize():
                writer_cls = writer_registry[(serialize_format, artifact.kind)]
                writer_cls(
                    data=artifact.data,
                    target_path=source.name,
                    timestamp=serializer.last_updated_ts,
                    metadata_store=metadata_store,
                ).write()


def process_source(source: SourceModel) -> RuleModel:
    aggregated_rules = RuleModel()

    for resource in source.resources:
        if isinstance(resource, SourceReference):
            referenced_source_name = resource.target
            aggregated_rules.merge_with(
                RuleModel.model_validate_json(
                    source_cache.retrieve(referenced_source_name)
                )
            )
        else:
            aggregated_rules.merge_with(process_resource(resource, source.option))
    aggregated_rules.filter(source.option)
    aggregated_rules.sort()
    source_cache.store(source.name, aggregated_rules.model_dump_json())
    return aggregated_rules


def process_resource(
    initial_resource: BaseResource, source_option: Option
) -> RuleModel:
    aggregated_rules = RuleModel()
    pending_resources = [initial_resource]

    for resource in pending_resources:
        cache_key = str(resource.source)
        if isinstance(resource, V2rayDomainResource):
            cache_key += f"::attrs={resource.option.attrs}"

        if cached_result := resource_cache.retrieve(cache_key):
            if isinstance(resource, V2rayDomainResource):
                parsed_rules = V2rayDomainResult.model_validate_json(cached_result)
            else:
                parsed_rules = RuleModel.model_validate_json(cached_result)
        else:
            if isinstance(resource, MaxMindDBResource):
                resource_data = fetcher.download_file(resource.source)
            else:
                resource_data = fetcher.get_content(resource.source)
            if isinstance(resource, V2rayDomainResource):
                parsed_rules = parse_data(resource_data, resource, resource.option)
            else:
                parsed_rules = parse_data(resource_data, resource, source_option)
            resource_cache.store(cache_key, parsed_rules.model_dump_json())

        if isinstance(parsed_rules, V2rayDomainResult):
            for include in parsed_rules.includes:
                included_resource = V2rayDomainResource(
                    source=build_v2ray_include_url(resource.source, include.name),
                    option=V2rayDomainOption(
                        attrs=V2rayDomainAttrs(
                            include_attrs=include.include_attrs
                            + resource.option.attrs.include_attrs,
                            exclude_attrs=include.exclude_attrs
                            + resource.option.attrs.exclude_attrs,
                        ),
                        exclude_includes=resource.option.exclude_includes,
                    ),
                )

                pending_resources.append(included_resource)
            parsed_rules = parsed_rules.rules

        aggregated_rules.merge_with(parsed_rules)
    return aggregated_rules


def main():
    try:
        metadata_store = MetadataStore()
        process_sources(SOURCES, metadata_store)
        metadata_store.save()
    except Exception as e:
        logger.exception(e)
        Path(".failure").touch()
