from collections.abc import Iterator

from loguru import logger
from pydantic import HttpUrl, ValidationError

from ..cache import Cache
from ..errors import ResourceError, UnknownResourceTypeError
from ..fetcher import fetcher
from ..models import (
    ContentResource,
    DomainSetResource,
    MaxMindDBResource,
    RuleModel,
    RuleSetResource,
    V2rayDomainResource,
    V2rayDomainResult,
)
from ..parsers import mmdb, v2ray_domain
from ..parsers.surge import DomainSetParser, RuleSetParser


class ResourceProcessor:
    def __init__(self, cache: Cache) -> None:
        self.cache: Cache = cache

    def iter_rule_models(
        self, initial_resource: ContentResource
    ) -> Iterator[RuleModel]:
        pending_resources = [initial_resource]

        for resource in pending_resources:
            parsed_rules = self.load(resource)

            if isinstance(parsed_rules, V2rayDomainResult):
                pending_resources.extend(parsed_rules.resources)
                parsed_rules = parsed_rules.rules

            yield parsed_rules

    def load(self, resource: ContentResource) -> RuleModel | V2rayDomainResult:
        cache_key = resource.cache_key()
        if (cached_result := self.cache.retrieve_text(cache_key)) is not None:
            try:
                if isinstance(resource, V2rayDomainResource):
                    return V2rayDomainResult.model_validate_json(cached_result)
                return RuleModel.model_validate_json(cached_result)
            except ValidationError as error:
                logger.warning(
                    f"Ignoring invalid cached rules for resource '{cache_key}': {error}"
                )

        if isinstance(resource, MaxMindDBResource):
            if not isinstance(resource.source, HttpUrl):
                raise ResourceError(
                    f"MaxMindDB resource requires an HTTP URL: {resource.source}"
                )
            parsed_rules = mmdb.parse(
                fetcher.download_file(resource.source),
                country_code=resource.option.country_code,
            )
        elif isinstance(resource, V2rayDomainResource):
            parsed_rules = v2ray_domain.parse(
                fetcher.get_content(resource.source), resource
            )
        elif isinstance(resource, RuleSetResource):
            parsed_rules = RuleSetParser(fetcher.get_content(resource.source)).parse()
        elif isinstance(resource, DomainSetResource):
            parsed_rules = DomainSetParser(fetcher.get_content(resource.source)).parse()
        else:
            raise UnknownResourceTypeError(resource)

        _ = self.cache.store(cache_key, parsed_rules.model_dump_json())
        return parsed_rules
