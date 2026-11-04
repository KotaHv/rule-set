from rule_set.models import (
    DomainType,
    V2rayDomainAttrs,
    V2rayDomainInclude,
    V2rayDomainOption,
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


def test_v2ray_regex_is_stored_separately_and_serialized():
    result = parse(r"regexp:^ads\.example\.com$", _option())

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

    result = parse(data, _option(exclude_includes=["blocked"]))

    assert result.includes == [
        V2rayDomainInclude(
            name="ads",
            include_attrs=["cn"],
            exclude_attrs=["ads"],
        ),
        V2rayDomainInclude(
            name="telemetry",
            include_attrs=[],
            exclude_attrs=["!cn"],
        ),
    ]
    assert result.rules.domain_trie.items() == []
    assert result.rules.domain_keyword == set()
    assert result.rules.domain_regex == set()


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
        _option(include_attrs=["cn"], exclude_attrs=["ads"]),
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

    result = parse(data, _option(include_attrs=["cn"]))

    assert set(result.rules.domain_trie.items()) == {
        ("commented.example", DomainType.DOMAIN_SUFFIX),
    }
    assert result.rules.domain_keyword == {"commented-keyword"}


def test_parse_prefixless_lines_default_to_domain_suffix():
    data = """
        plain.example
        plain-with-attrs.example @cn # trailing comment
    """

    result = parse(data, _option())

    assert set(result.rules.domain_trie.items()) == {
        ("plain.example", DomainType.DOMAIN_SUFFIX),
        ("plain-with-attrs.example", DomainType.DOMAIN_SUFFIX),
    }
