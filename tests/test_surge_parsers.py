import pytest

from rule_set.models import DomainType
from rule_set.models.logical import LogicalOperator, Rule
from rule_set.parsers.surge import DomainSetParser, RuleSetParser


def test_domain_set_parser_maps_domains_comments_and_invalid_lines():
    data = """
        # hash comment
        ; semicolon comment
        // slash comment
        .example.com
        plain.example
        inline-hash.example # trailing comment
        inline-semicolon.example ; trailing comment
        inline-slash.example//trailing comment
        //ignored.example
        -bad.example
        .-bad.example
        example..com
    """

    result = DomainSetParser(data).parse()

    assert set(result.domain_trie.items()) == {
        ("example.com", DomainType.DOMAIN_SUFFIX),
        ("plain.example", DomainType.DOMAIN),
        ("inline-hash.example", DomainType.DOMAIN),
        ("inline-semicolon.example", DomainType.DOMAIN),
        ("inline-slash.example", DomainType.DOMAIN),
    }


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("DOMAIN,exact.example.com", {"domain": ["exact.example.com"]}),
        (
            "DOMAIN-SUFFIX,suffix.example.com",
            {"domain_suffix": ["suffix.example.com"]},
        ),
        ("DOMAIN-KEYWORD,keyword", {"domain_keyword": ["keyword"]}),
        (
            "DOMAIN-WILDCARD,*.wild.example.com",
            {"domain_wildcard": ["*.wild.example.com"]},
        ),
        ("IP-CIDR,1.1.1.0/24,no-resolve", {"ip_cidr": ["1.1.1.0/24"]}),
        ("IP-CIDR6,2001:db8::/32,no-resolve", {"ip_cidr6": ["2001:db8::/32"]}),
        ("IP-ASN,13335", {"ip_asn": ["13335"]}),
        ("USER-AGENT,MyAgent*", {"user_agent": ["MyAgent*"]}),
        ("PROCESS-NAME,curl", {"process": ["curl"]}),
        (
            r"URL-REGEX,^https?://example\.com/ads",
            {"url_regex": [r"^https?://example\.com/ads"]},
        ),
        (
            r"URL-REGEX,^ftp://example\.com/ads",
            {"url_regex": [r"^ftp://example\.com/ads"]},
        ),
    ],
)
def test_rule_set_parser_parses_supported_rule_types(line, expected):
    result = RuleSetParser(line).parse().to_serializable_rule_model()

    for field, values in expected.items():
        assert getattr(result, field) == values


def test_rule_set_parser_parses_logical_rules():
    result = RuleSetParser(
        "AND,((DOMAIN-SUFFIX,example.com),(DOMAIN-KEYWORD,ads))"
    ).parse()

    tree = next(iter(result.logical))
    assert tree.root.op is LogicalOperator.AND
    children = tuple(child for child in tree.root.children if isinstance(child, Rule))
    assert len(children) == len(tree.root.children)
    assert [child.rule.rule_values for child in children] == [
        ("example.com",),
        ("ads",),
    ]


def test_rule_set_parser_skips_invalid_and_unknown_rules_and_continues():
    result = RuleSetParser(
        """
        UNKNOWN-TYPE,ignored
        DOMAIN,-bad.example
        DOMAIN-SUFFIX,example..com
        AND,((DOMAIN-SUFFIX,example.com))
        DOMAIN,kept.example.com
        """
    ).parse()

    assert set(result.domain_trie.items()) == {
        ("kept.example.com", DomainType.DOMAIN),
    }
    assert result.logical == set()
