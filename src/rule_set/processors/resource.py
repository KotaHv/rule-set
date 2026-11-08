from collections.abc import Iterator

from pydantic import HttpUrl

from ..cache import Cache
from ..errors import ResourceError, UnknownResourceTypeError
from ..fetcher import fetcher
from ..models import (
    ContentResource,
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
        self.cache: Cache = cache

    def iter_rule_models(
        self, initial_resource: ContentResource, source_option: Option
    ) -> Iterator[RuleModel]:
        pending_resources = [initial_resource]

        for resource in pending_resources:
            parsed_rules = self._get_rules(resource, source_option)

            if isinstance(parsed_rules, V2rayDomainResult):
                assert isinstance(resource, V2rayDomainResource)
                pending_resources.extend(
                    self._build_v2ray_include_resources(resource, parsed_rules)
                )
                parsed_rules = parsed_rules.rules

            yield parsed_rules

    def _get_rules(
        self, resource: ContentResource, source_option: Option
    ) -> RuleModel | V2rayDomainResult:
        cache_key = self._cache_key(resource, source_option)
        if (cached_result := self.cache.retrieve_text(cache_key)) is not None:
            if isinstance(resource, V2rayDomainResource):
                return V2rayDomainResult.model_validate_json(cached_result)
            return RuleModel.model_validate_json(cached_result)

        if isinstance(resource, MaxMindDBResource):
            if not isinstance(resource.source, HttpUrl):
                raise ResourceError(
                    f"MaxMindDB resource requires an HTTP URL: {resource.source}"
                )
            parsed_rules = mmdb.parse(
                fetcher.download_file(resource.source),
                country_code=source_option.geo_ip.country_code,
            )
        elif isinstance(resource, V2rayDomainResource):
            parsed_rules = v2ray_domain.parse(
                fetcher.get_content(resource.source), resource.option
            )
        elif isinstance(resource, RuleSetResource):
            parsed_rules = RuleSetParser(fetcher.get_content(resource.source)).parse()
        elif isinstance(resource, DomainSetResource):
            parsed_rules = DomainSetParser(fetcher.get_content(resource.source)).parse()
        else:
            raise UnknownResourceTypeError(resource)

        _ = self.cache.store(cache_key, parsed_rules.model_dump_json())
        return parsed_rules

    @staticmethod
    def _cache_key(resource: ContentResource, source_option: Option) -> str:
        cache_key = str(resource.source)
        if isinstance(resource, V2rayDomainResource):
            cache_key += f"::attrs={resource.option.attrs}"
        elif isinstance(resource, MaxMindDBResource):
            cache_key += f"::country_code={source_option.geo_ip.country_code}"
        return cache_key

    @staticmethod
    def _build_v2ray_include_resources(
        resource: V2rayDomainResource, result: V2rayDomainResult
    ) -> list[V2rayDomainResource]:
        if not isinstance(resource.source, HttpUrl):
            raise ResourceError(
                f"Cannot resolve includes for non-HTTP source: {resource.source}"
            )
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
