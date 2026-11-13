from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from time import time

from loguru import logger
from pydantic import ValidationError

from ..cache import Cache
from ..config import settings
from ..errors import ResourceError, SerializerError, UnknownResourceTypeError
from ..file_writers import write_if_changed
from ..metadata import MetadataStore
from ..models import (
    ContentResource,
    MetadataRecord,
    RuleModel,
    SerializableRuleModel,
    SerializeFormat,
    SourceModel,
    SourceReference,
)
from ..output import (
    CLASH_MRS_OUTPUTS,
    CLASH_OUTPUTS,
    EGERN_OUTPUT,
    GEOIP_OUTPUT,
    LOON_OUTPUT,
    SING_BOX_OUTPUT,
    SING_BOX_SRS_OUTPUT,
    SURGE_OUTPUT,
    OutputSpec,
)
from ..serializers.clients import (
    BaseRuleSerializer,
    ClashMrsSerializer,
    ClashPayload,
    ClashPayloadSerializer,
    ClashYamlSerializer,
    EgernSerializer,
    GeoIPSerializer,
    LoonSerializer,
    SingBoxJsonSerializer,
    SingBoxRuleSetSerializer,
    SingBoxSrsSerializer,
    SurgeSerializer,
)
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

    def build(self, source: SourceModel) -> None:
        rules = self._resolve_rules(source)
        serializable_rules = rules.to_serializable_rule_model()
        timestamp = time()
        last_updated = datetime.fromtimestamp(timestamp, tz=UTC).isoformat()

        for serialize_format in self._resolve_formats(source):
            match serialize_format:
                case SerializeFormat.Clash:
                    self._build_clash_outputs(
                        serializable_rules, source, timestamp, last_updated
                    )
                case SerializeFormat.Sing_Box:
                    self._build_sing_box_outputs(
                        serializable_rules, source, timestamp, last_updated
                    )
                case SerializeFormat.Surge:
                    self._build_output(
                        SurgeSerializer,
                        SURGE_OUTPUT,
                        serializable_rules,
                        source,
                        timestamp,
                        last_updated,
                    )
                case SerializeFormat.Loon:
                    self._build_output(
                        LoonSerializer,
                        LOON_OUTPUT,
                        serializable_rules,
                        source,
                        timestamp,
                        last_updated,
                    )
                case SerializeFormat.Egern:
                    self._build_output(
                        EgernSerializer,
                        EGERN_OUTPUT,
                        serializable_rules,
                        source,
                        timestamp,
                        last_updated,
                    )
                case SerializeFormat.GeoIP:
                    self._build_output(
                        GeoIPSerializer,
                        GEOIP_OUTPUT,
                        serializable_rules,
                        source,
                        timestamp,
                        last_updated,
                    )

    def _build_output(
        self,
        serializer_cls: type[BaseRuleSerializer[str | bytes]],
        output: OutputSpec,
        rules: SerializableRuleModel,
        source: SourceModel,
        timestamp: float,
        last_updated: str,
    ) -> None:
        serializer = serializer_cls(option=source.option, last_updated=last_updated)
        data = serializer.serialize(rules)
        _ = self._persist_output(
            output.path(source.name),
            data,
            timestamp=timestamp,
        )

    def _build_sing_box_outputs(
        self,
        rules: SerializableRuleModel,
        source: SourceModel,
        timestamp: float,
        last_updated: str,
    ) -> None:
        rule_set = SingBoxRuleSetSerializer(
            option=source.option,
            last_updated=last_updated,
        ).serialize(rules)
        if not rule_set["rules"]:
            return

        changed = self._persist_output(
            SING_BOX_OUTPUT.path(source.name),
            SingBoxJsonSerializer().serialize(rule_set),
            timestamp=timestamp,
        )

        srs_path = SING_BOX_SRS_OUTPUT.path(source.name)
        if changed or not srs_path.exists():
            _ = self._persist_output(
                srs_path,
                SingBoxSrsSerializer().serialize(rule_set),
                timestamp=timestamp,
            )

    def _build_clash_outputs(
        self,
        rules: SerializableRuleModel,
        source: SourceModel,
        timestamp: float,
        last_updated: str,
    ) -> None:
        payloads = ClashPayloadSerializer(
            option=source.option,
            last_updated=last_updated,
        ).serialize(rules)
        yaml_serializer = ClashYamlSerializer(last_updated=last_updated)
        mrs_serializer = ClashMrsSerializer()

        for payload in payloads:
            self._build_clash_payload(
                payload,
                source=source,
                timestamp=timestamp,
                yaml_serializer=yaml_serializer,
                mrs_serializer=mrs_serializer,
            )

    def _build_clash_payload(
        self,
        payload: ClashPayload,
        *,
        source: SourceModel,
        timestamp: float,
        yaml_serializer: ClashYamlSerializer,
        mrs_serializer: ClashMrsSerializer,
    ) -> None:
        yaml_output = CLASH_OUTPUTS.get(payload.kind)
        if yaml_output is None:
            raise SerializerError(f"unsupported Clash payload kind: {payload.kind}")

        changed = self._persist_output(
            yaml_output.path(source.name),
            yaml_serializer.serialize(payload),
            timestamp=timestamp,
        )

        mrs_output = CLASH_MRS_OUTPUTS.get(payload.kind)
        if mrs_output is None:
            return

        mrs_path = mrs_output.path(source.name)
        if changed or not mrs_path.exists():
            _ = self._persist_output(
                mrs_path,
                mrs_serializer.serialize(payload),
                timestamp=timestamp,
            )

    def _persist_output(
        self,
        filepath: Path,
        data: str | bytes,
        *,
        timestamp: float,
    ) -> bool:
        if not write_if_changed(filepath, data):
            return False
        self.metadata_store.update(
            MetadataRecord(
                path=filepath.relative_to(settings.build_dir),
                timestamp=timestamp,
            )
        )
        return True

    def _resolve_rules(self, source: SourceModel) -> RuleModel:
        if (
            cached_result := self.cache.retrieve_text(source.name.as_posix())
        ) is not None:
            try:
                return RuleModel.model_validate_json(cached_result, strict=True)
            except ValidationError as error:
                logger.warning(
                    f"Ignoring invalid cached rules for source '{source.name}': {error}"
                )
        return self._build_rules(source)

    def _build_rules(self, source: SourceModel) -> RuleModel:
        aggregated_rules = RuleModel.merge_all(self._iter_rule_models(source))
        with logger.contextualize(source=source.name):
            aggregated_rules.filter(source.option)
        _ = self.cache.store(source.name.as_posix(), aggregated_rules.model_dump_json())
        return aggregated_rules

    def _iter_rule_models(self, source: SourceModel) -> Iterator[RuleModel]:
        for resource in source.resources:
            if isinstance(resource, SourceReference):
                cached_result = self.cache.retrieve_text(resource.target)
                if cached_result is None:
                    raise ResourceError(
                        f"Missing cached rules for referenced source '{resource.target}'"
                    )
                try:
                    yield RuleModel.model_validate_json(cached_result)
                except ValidationError as error:
                    raise ResourceError(
                        f"Invalid cached rules for referenced source '{resource.target}'"
                    ) from error
            elif isinstance(resource, ContentResource):
                yield from self.resource_processor.iter_rule_models(resource)
            else:
                raise UnknownResourceTypeError(resource)

    @staticmethod
    def _resolve_formats(source: SourceModel) -> list[SerializeFormat]:
        if source.include:
            return source.include
        return [
            serialize_format
            for serialize_format in SerializeFormat
            if serialize_format not in source.exclude
            and not (
                source.option.geo_ip.country_code is None
                and serialize_format == SerializeFormat.GeoIP
            )
        ]
