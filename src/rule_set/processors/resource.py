from pathlib import Path

from ..cache import Cache
from ..errors import UnknownResourceTypeError
from ..fetcher import fetcher
from ..models import (
    BaseResource,
    DomainSetResource,
    MaxMindDBResource,
    Option,
    RuleModel,
    RuleSetResource,
    V2rayDomainAttrs,
    V2rayDomainOption,
    V2rayDomainResource,
    V2rayDomainResult,
)
from ..parsers import mmdb, v2ray_domain
from ..parsers.surge import DomainSetParser, RuleSetParser
from ..utils import build_v2ray_include_url


class ResourceProcessor:
    def __init__(self, cache: Cache) -> None:
        self.cache = cache

    def process(
        self, initial_resource: BaseResource, source_option: Option
    ) -> RuleModel:
        aggregated_rules = RuleModel()
        pending_resources = [initial_resource]

        for resource in pending_resources:
            parsed_rules = self._get_rules(resource, source_option)

            if isinstance(parsed_rules, V2rayDomainResult):
                assert isinstance(resource, V2rayDomainResource)
                pending_resources.extend(
                    self._build_v2ray_include_resources(resource, parsed_rules)
                )
                parsed_rules = parsed_rules.rules

            aggregated_rules.merge_with(parsed_rules)
        return aggregated_rules

    def _get_rules(
        self, resource: BaseResource, source_option: Option
    ) -> RuleModel | V2rayDomainResult:
        cache_key = self._cache_key(resource)
        if cached_result := self.cache.retrieve(cache_key):
            if isinstance(resource, V2rayDomainResource):
                return V2rayDomainResult.model_validate_json(cached_result)
            return RuleModel.model_validate_json(cached_result)

        if isinstance(resource, MaxMindDBResource):
            resource_data = fetcher.download_file(resource.source)
        else:
            resource_data = fetcher.get_content(resource.source)

        if isinstance(resource, V2rayDomainResource):
            parsed_rules = self._parse_data(resource_data, resource, resource.option)
        else:
            parsed_rules = self._parse_data(resource_data, resource, source_option)
        self.cache.store(cache_key, parsed_rules.model_dump_json())
        return parsed_rules

    @staticmethod
    def _cache_key(resource: BaseResource) -> str:
        cache_key = str(resource.source)
        if isinstance(resource, V2rayDomainResource):
            cache_key += f"::attrs={resource.option.attrs}"
        return cache_key

    @staticmethod
    def _parse_data(
        resource_data: str | list | Path,
        resource: BaseResource,
        option: Option | V2rayDomainOption,
    ) -> RuleModel | V2rayDomainResult:
        if isinstance(resource, RuleSetResource):
            return RuleSetParser(resource_data).parse()
        if isinstance(resource, DomainSetResource):
            return DomainSetParser(resource_data).parse()
        if isinstance(resource, MaxMindDBResource):
            return mmdb.parse(resource_data, country_code=option.geo_ip.country_code)
        if isinstance(resource, V2rayDomainResource):
            return v2ray_domain.parse(resource_data, option)
        raise UnknownResourceTypeError(resource)

    @staticmethod
    def _build_v2ray_include_resources(
        resource: V2rayDomainResource, result: V2rayDomainResult
    ) -> list[V2rayDomainResource]:
        return [
            V2rayDomainResource(
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
            for include in result.includes
        ]
