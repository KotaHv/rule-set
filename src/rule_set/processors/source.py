from ..cache import Cache
from ..errors import ResourceError, UnknownResourceTypeError
from ..file_writers import writer_registry
from ..metadata import MetadataStore
from ..models import (
    ContentResource,
    RuleModel,
    SerializeFormat,
    SourceModel,
    SourceReference,
)
from ..serializers.clients import client_serializers
from .resource import ResourceProcessor


class SourceProcessor:
    def __init__(
        self,
        cache: Cache,
        resource_processor: ResourceProcessor,
        metadata_store: MetadataStore,
    ) -> None:
        self.cache: Cache = cache
        self.resource_processor: ResourceProcessor = resource_processor
        self.metadata_store: MetadataStore = metadata_store

    def process(self, source: SourceModel) -> None:
        rules = self._get_rules(source)
        serializable_rules = rules.to_serializable_rule_model()

        for serialize_format in self._get_serialize_formats(source):
            serializer_cls = client_serializers[serialize_format]
            serializer = serializer_cls(rules=serializable_rules, option=source.option)
            for artifact in serializer.serialize():
                writer_cls = writer_registry[(serialize_format, artifact.kind)]
                _ = writer_cls(
                    data=artifact.data,
                    target_path=source.name,
                    timestamp=serializer.last_updated_ts,
                    metadata_store=self.metadata_store,
                ).write()

    def _get_rules(self, source: SourceModel) -> RuleModel:
        if (
            cached_result := self.cache.retrieve_text(source.name.as_posix())
        ) is not None:
            return RuleModel.model_validate_json(cached_result, strict=True)
        return self._process_rules(source)

    def _process_rules(self, source: SourceModel) -> RuleModel:
        aggregated_rules = RuleModel()

        for resource in source.resources:
            if isinstance(resource, SourceReference):
                cached_result = self.cache.retrieve_text(resource.target)
                if cached_result is None:
                    raise ResourceError(
                        f"Missing cached rules for referenced source '{resource.target}'"
                    )
                aggregated_rules.merge_with(
                    RuleModel.model_validate_json(cached_result)
                )
            elif isinstance(resource, ContentResource):
                aggregated_rules.merge_with(
                    self.resource_processor.process(resource, source.option)
                )
            else:
                raise UnknownResourceTypeError(resource)
        aggregated_rules.filter(source.option)
        _ = self.cache.store(source.name.as_posix(), aggregated_rules.model_dump_json())
        return aggregated_rules

    @staticmethod
    def _get_serialize_formats(source: SourceModel) -> list[SerializeFormat]:
        if source.include:
            return source.include
        return [
            serialize_format
            for serialize_format in client_serializers
            if serialize_format not in source.exclude
            and not (
                source.option.geo_ip.country_code is None
                and serialize_format == SerializeFormat.GeoIP
            )
        ]
