from pathlib import Path

from loguru import logger

from .cache import Cache
from .file_writers import writer_registry
from .metadata import MetadataStore
from .models import (
    RuleModel,
    SerializeFormat,
    SourceModel,
    SourceReference,
)
from .processors import ResourceProcessor
from .serializers.clients import client_serializers
from .sources import SOURCES

resource_processor = ResourceProcessor(Cache(path="resource"))
source_cache = Cache(path="source")


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
            aggregated_rules.merge_with(
                resource_processor.process(resource, source.option)
            )
    aggregated_rules.filter(source.option)
    aggregated_rules.sort()
    source_cache.store(source.name, aggregated_rules.model_dump_json())
    return aggregated_rules


def main():
    try:
        metadata_store = MetadataStore()
        process_sources(SOURCES, metadata_store)
        metadata_store.save()
    except Exception as e:
        logger.exception(e)
        Path(".failure").touch()
