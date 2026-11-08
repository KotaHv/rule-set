from pathlib import Path

from pydantic import HttpUrl

from rule_set.models import (
    DomainType,
    Option,
    ResourceList,
    SourceModel,
    V2rayDomainAttrs,
    V2rayDomainOption,
    V2rayDomainResource,
    V2rayDomainResult,
)
from rule_set.parsers.v2ray_domain import parse


def _option(
    *,
    include_attrs: list[str] | None = None,
    exclude_attrs: list[str] | None = None,
    exclude_includes: list[str] | None = None,
) -> V2rayDomainOption:
    return V2rayDomainOption(
        attrs=V2rayDomainAttrs(
            include_attrs=include_attrs or [],
            exclude_attrs=exclude_attrs or [],
        ),
        exclude_includes=exclude_includes or [],
    )


def _resource(
    *,
    include_attrs: list[str] | None = None,
    exclude_attrs: list[str] | None = None,
    exclude_includes: list[str] | None = None,
    source: str = "https://example.com/list",
) -> V2rayDomainResource:
    return V2rayDomainResource(
        source=HttpUrl(source),
        option=_option(
            include_attrs=include_attrs,
            exclude_attrs=exclude_attrs,
            exclude_includes=exclude_includes,
        ),
    )


def _source(resource_option: V2rayDomainOption | None = None) -> SourceModel:
    resources: ResourceList = [
        V2rayDomainResource(
            source=HttpUrl("https://example.com/list"),
            option=(
                V2rayDomainOption() if resource_option is None else resource_option
            ),
        )
    ]
    return SourceModel(
        name=Path("test"),
        resources=resources,
        option=Option(
            v2ray_domain=V2rayDomainOption(
                attrs=V2rayDomainAttrs(include_attrs=["cn"]),
                exclude_includes=["blocked"],
            )
        ),
    )


def test_resource_inherits_both_fields_when_unset():
    resource = _source().resources[0]
    assert isinstance(resource, V2rayDomainResource)

    assert resource.option.attrs.include_attrs == ["@cn"]
    assert resource.option.exclude_includes == ["blocked"]


def test_resource_inherits_only_unset_field():
    resource = _source(V2rayDomainOption(exclude_includes=[])).resources[0]
    assert isinstance(resource, V2rayDomainResource)

    assert resource.option.attrs.include_attrs == ["@cn"]
    assert resource.option.exclude_includes == []


def test_resource_keeps_explicit_empty_values():
    resource = _source(
        V2rayDomainOption(
            attrs=V2rayDomainAttrs(exclude_attrs=["ads"]),
            exclude_includes=[],
        )
    ).resources[0]
    assert isinstance(resource, V2rayDomainResource)

    assert resource.option.attrs.include_attrs == []
    assert resource.option.attrs.exclude_attrs == ["@ads"]
    assert resource.option.exclude_includes == []


def test_v2ray_regex_is_stored_separately_and_serialized():
    result = parse(r"regexp:^ads\.example\.com$", _resource())

    assert result.rules.domain_trie.items() == []
    assert result.rules.domain_regex == {r"^ads\.example\.com$"}
    assert result.rules.to_serializable_rule_model().domain_regex == [
        r"^ads\.example\.com$"
    ]


def test_parse_include_rules_with_attributes_and_exclude_includes():
    data = """
        include:ads @cn @-ads
        include:blocked
        include:telemetry @-!cn # inline comment
    """

    result = parse(
        data,
        _resource(
            include_attrs=["parent-cn"],
            exclude_attrs=["parent-ads"],
            exclude_includes=["blocked"],
        ),
    )

    assert result.resources == [
        V2rayDomainResource(
            source=HttpUrl("https://example.com/ads"),
            option=V2rayDomainOption(
                attrs=V2rayDomainAttrs(
                    include_attrs=["cn", "parent-cn"],
                    exclude_attrs=["ads", "parent-ads"],
                ),
                exclude_includes=["blocked"],
            ),
        ),
        V2rayDomainResource(
            source=HttpUrl("https://example.com/telemetry"),
            option=V2rayDomainOption(
                attrs=V2rayDomainAttrs(
                    include_attrs=["parent-cn"],
                    exclude_attrs=["!cn", "parent-ads"],
                ),
                exclude_includes=["blocked"],
            ),
        ),
    ]
    assert result.rules.domain_trie.items() == []
    assert result.rules.domain_keyword == set()
    assert result.rules.domain_regex == set()


def test_parse_include_resolves_relative_to_local_source():
    resource = V2rayDomainResource(
        source=Path("lists/main.txt"),
        option=_option(),
    )

    result = parse("include:ads @cn", resource)

    assert result.resources == [
        V2rayDomainResource(
            source=Path("lists/ads"),
            option=V2rayDomainOption(
                attrs=V2rayDomainAttrs(include_attrs=["cn"]),
            ),
        )
    ]


def test_v2ray_result_cache_roundtrip_preserves_http_source():
    result = parse("include:ads", _resource())

    restored = V2rayDomainResult.model_validate_json(result.model_dump_json())

    assert restored.resources == result.resources
    assert isinstance(restored.resources[0].source, HttpUrl)


def test_parse_attribute_matching_applies_to_all_rule_types():
    data = r"""
        domain:included.example @cn
        domain:excluded.example @cn @ads
        domain:unmatched.example @global
        keyword:included-keyword @cn
        keyword:unmatched-keyword @global
        full:www.full.example @cn
        full:www.unmatched.example @global
        regexp:^included\. @cn
        regexp:^unmatched\. @global
    """

    result = parse(
        data,
        _resource(include_attrs=["cn"], exclude_attrs=["ads"]),
    )

    assert set(result.rules.domain_trie.items()) == {
        ("included.example", DomainType.DOMAIN_SUFFIX),
        ("www.full.example", DomainType.DOMAIN),
    }
    assert result.rules.domain_keyword == {"included-keyword"}
    assert result.rules.domain_regex == {r"^included\."}


def test_parse_inline_comments_are_ignored():
    data = """
        # comment-only line
        domain:commented.example @cn # trailing comment
        keyword:commented-keyword @cn # trailing comment
        filtered.example # @cn stays part of the comment
    """

    result = parse(data, _resource(include_attrs=["cn"]))

    assert set(result.rules.domain_trie.items()) == {
        ("commented.example", DomainType.DOMAIN_SUFFIX),
    }
    assert result.rules.domain_keyword == {"commented-keyword"}


def test_parse_prefixless_lines_default_to_domain_suffix():
    data = """
        plain.example
        plain-with-attrs.example @cn # trailing comment
    """

    result = parse(data, _resource())

    assert set(result.rules.domain_trie.items()) == {
        ("plain.example", DomainType.DOMAIN_SUFFIX),
        ("plain-with-attrs.example", DomainType.DOMAIN_SUFFIX),
    }


def test_parse_skips_invalid_domain_rules():
    data = """
        domain:valid-suffix.example
        domain:-invalid.example
        domain:example..com
        full:valid-full.example
        full:-invalid.example
        full:example..com
    """

    result = parse(data, _resource())

    assert set(result.rules.domain_trie.items()) == {
        ("valid-suffix.example", DomainType.DOMAIN_SUFFIX),
        ("valid-full.example", DomainType.DOMAIN),
    }
