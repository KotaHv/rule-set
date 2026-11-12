import pytest

from rule_set.models import (
    Option,
    ProcessingOption,
    ProcessingRuleType,
    RuleModel,
)
from rule_set.models.logical import (
    ConcreteRule,
    Logical,
    LogicalOperator,
    LogicalTree,
    Rule,
    RuleType,
)


def _and(*values: str) -> LogicalTree:
    return LogicalTree(
        root=Logical(
            op=LogicalOperator.AND,
            children=tuple(
                Rule(rule=ConcreteRule(rule_type=RuleType.DOMAIN, rule_values=(value,)))
                for value in values
            ),
        )
    )


def _domain_values(tree: LogicalTree) -> tuple[str, ...]:
    return tuple(
        child.rule.rule_values[0]
        for child in tree.root.children
        if isinstance(child, Rule)
    )


def test_domain_regex_removes_covered_domains_only():
    rules = RuleModel(
        domain={
            "ads.example.com",
            "www.tracking.example.com",
            "keep.example.com",
        },
        domain_suffix={"ads.example.net"},
        domain_regex={r"^ads\.", r"\.tracking\."},
    )

    rules.filter(Option())

    assert rules.domain == {"keep.example.com"}
    assert rules.domain_suffix == {"ads.example.net"}


def test_invalid_domain_regex_does_not_break_filtering():
    rules = RuleModel(domain={"ads.example.com"}, domain_regex={r"[invalid"})

    rules.filter(Option())

    assert rules.domain == {"ads.example.com"}


def test_merge_with_merges_rule_collections():
    rules = RuleModel.model_validate(
        {
            "domain": {"a.example.com"},
            "domain_suffix": {"a.example.net"},
            "domain_wildcard": {"*.a.example.org"},
            "domain_regex": {r"^a\."},
            "domain_keyword": {"ads"},
            "ip_cidr": {"1.1.1.0/24"},
            "ip_cidr6": {"2001:db8::/32"},
            "ip_asn": {"13335"},
            "process": {"first-process"},
            "user_agent": {"first-agent"},
            "url_regex": {"first-url"},
        }
    )
    other = RuleModel.model_validate(
        {
            "domain": {"b.example.com"},
            "domain_suffix": {"b.example.net"},
            "domain_wildcard": {"*.b.example.org"},
            "domain_regex": {r"^b\."},
            "domain_keyword": {"tracking"},
            "ip_cidr": {"2.2.2.0/24"},
            "ip_cidr6": {"2001:db9::/32"},
            "ip_asn": {"15169"},
            "process": {"second-process"},
            "user_agent": {"second-agent"},
            "url_regex": {"second-url"},
        }
    )

    rules.merge_with(other)

    assert rules.domain == {"a.example.com", "b.example.com"}
    assert rules.domain_suffix == {"a.example.net", "b.example.net"}
    assert rules.domain_wildcard == {"*.a.example.org", "*.b.example.org"}
    assert rules.domain_regex == {r"^a\.", r"^b\."}
    assert rules.domain_keyword == {"ads", "tracking"}
    assert rules.ip_cidr == {"1.1.1.0/24", "2.2.2.0/24"}
    assert rules.ip_cidr6 == {"2001:db8::/32", "2001:db9::/32"}
    assert rules.ip_asn == {"13335", "15169"}
    assert rules.process == {"first-process", "second-process"}
    assert rules.user_agent == {"first-agent", "second-agent"}
    assert rules.url_regex == {"first-url", "second-url"}


def test_merge_all_combines_models_and_handles_empty():
    first = RuleModel(domain_regex={r"^a\."})
    second = RuleModel(domain_regex={r"^b\."})

    merged = RuleModel.merge_all([first, second])

    assert merged.domain_regex == {r"^a\.", r"^b\."}
    assert RuleModel.merge_all([]).domain_regex == set()


def _populated_rules() -> RuleModel:
    rules = RuleModel.model_validate(
        {
            "domain": {"example.com"},
            "domain_suffix": {"example.net"},
            "domain_wildcard": {"*.example.org"},
            "domain_regex": {r"^ads\."},
            "domain_keyword": {"tracking"},
            "ip_cidr": {"1.1.1.0/24"},
            "ip_cidr6": {"2001:db8::/32"},
            "ip_asn": {"13335"},
            "process": {"curl"},
            "user_agent": {"agent"},
            "url_regex": {"^https://"},
        }
    )
    rules.logical.add(_and("b", "d"))
    return rules


def _rule_type_state(rules: RuleModel) -> dict[ProcessingRuleType, list[str]]:
    return {
        ProcessingRuleType.DOMAIN: sorted(rules.domain),
        ProcessingRuleType.DOMAIN_SUFFIX: sorted(rules.domain_suffix),
        ProcessingRuleType.DOMAIN_WILDCARD: sorted(rules.domain_wildcard),
        ProcessingRuleType.DOMAIN_REGEX: sorted(rules.domain_regex),
        ProcessingRuleType.DOMAIN_KEYWORD: sorted(rules.domain_keyword),
        ProcessingRuleType.IP_CIDR: sorted(rules.ip_cidr),
        ProcessingRuleType.IP_CIDR6: sorted(rules.ip_cidr6),
        ProcessingRuleType.IP_ASN: sorted(rules.ip_asn, key=int),
        ProcessingRuleType.LOGICAL: sorted(
            tree.model_dump_json() for tree in rules.logical
        ),
        ProcessingRuleType.PROCESS_NAME: sorted(rules.process),
        ProcessingRuleType.USER_AGENT: sorted(rules.user_agent),
        ProcessingRuleType.URL_REGEX: sorted(rules.url_regex),
    }


@pytest.mark.parametrize("rule_type", list(ProcessingRuleType))
def test_filter_clears_each_rule_type(rule_type: ProcessingRuleType):
    rules = _populated_rules()
    before = _rule_type_state(rules)
    assert set(before) == set(ProcessingRuleType)
    assert before[rule_type], f"{rule_type} fixture is empty"

    rules.filter(Option(processing=ProcessingOption(exclude_rule_types=[rule_type])))

    after = _rule_type_state(rules)
    expected = before.copy()
    expected[rule_type] = []
    assert after == expected


def test_filter_includes_only_requested_rule_types():
    rules = _populated_rules()

    rules.filter(
        Option(
            processing=ProcessingOption(
                include_rule_types=[
                    ProcessingRuleType.DOMAIN_SUFFIX,
                    ProcessingRuleType.IP_CIDR,
                ]
            )
        )
    )

    assert rules.domain == set()
    assert rules.domain_suffix == {"example.net"}
    assert rules.domain_wildcard == set()
    assert rules.ip_cidr == {"1.1.1.0/24"}
    assert rules.ip_cidr6 == set()
    assert rules.domain_regex == set()
    assert rules.domain_keyword == set()
    assert rules.ip_asn == set()
    assert rules.logical == set()
    assert rules.process == set()
    assert rules.user_agent == set()
    assert rules.url_regex == set()


def test_filter_includes_domain_even_when_suffix_is_removed():
    rules = RuleModel(domain={"a.example.com"}, domain_suffix={"example.com"})

    rules.filter(
        Option(
            processing=ProcessingOption(include_rule_types=[ProcessingRuleType.DOMAIN])
        )
    )

    assert rules.domain == {"a.example.com"}
    assert rules.domain_suffix == set()


def test_filter_excludes_suffixes_from_all_domain_sets():
    rules = RuleModel(
        domain={"example.com", "www.example.com", "notexample.com", "keep.example.net"},
        domain_suffix={"suffix.example.com", "suffix.example.net"},
        domain_wildcard={"*.example.com", "*.example.org"},
    )

    rules.filter(
        Option(
            processing=ProcessingOption(
                exclude_suffixes=["example.com", "missing.example"]
            )
        )
    )

    assert rules.domain == {"notexample.com", "keep.example.net"}
    assert rules.domain_suffix == {"suffix.example.net"}
    assert rules.domain_wildcard == {"*.example.org"}


def test_filter_deduplicates_domain_keywords():
    rules = RuleModel(domain_keyword={"ads", "ads.example.com", "tracking"})

    rules.filter(Option())

    assert rules.domain_keyword == {"ads", "tracking"}


def test_filter_applies_keywords_to_all_domain_sets_and_regex():
    rules = RuleModel(
        domain={"ads.example.net", "keep.example.net"},
        domain_suffix={"ads.example.org", "keep.example.org"},
        domain_wildcard={"ads*.example.com", "keep*.example.com"},
        domain_regex={r"^ads\.example\.com$", r"^keep\.example\.com$"},
    )

    rules.filter(Option(processing=ProcessingOption(exclude_keywords=["ads"])))

    assert rules.domain == {"keep.example.net"}
    assert rules.domain_suffix == {"keep.example.org"}
    assert rules.domain_wildcard == {"keep*.example.com"}
    assert rules.domain_regex == {r"^keep\.example\.com$"}


def test_filter_removes_domains_covered_by_suffix():
    rules = RuleModel(
        domain={"a.example.com", "example.com", "other.net"},
        domain_suffix={"example.com"},
    )

    rules.filter(Option())

    assert rules.domain == {"other.net"}
    assert rules.domain_suffix == {"example.com"}


def test_filter_removes_rules_covered_by_wildcard():
    rules = RuleModel(
        domain={"bar.foo.com", "keep.example.com"},
        domain_suffix={"bar2.foo.com", "keep.net"},
        domain_wildcard={"*.foo.com"},
    )

    rules.filter(Option())

    assert rules.domain == {"keep.example.com"}
    assert rules.domain_suffix == {"keep.net"}
    assert rules.domain_wildcard == {"*.foo.com"}


def test_filter_keeps_suffix_not_covered_by_wildcard():
    rules = RuleModel(
        domain_suffix={"ads-api.tiktok.com"},
        domain_wildcard={"ads-*.tiktok.com"},
    )

    rules.filter(Option())

    assert rules.domain_suffix == {"ads-api.tiktok.com"}
    assert rules.domain_wildcard == {"ads-*.tiktok.com"}


def test_filter_deduplicates_ip_cidrs():
    rules = RuleModel(
        ip_cidr={"10.1.0.0/16", "10.0.0.0/8", "1.1.1.0/24", "1.1.1.1/24"},
        ip_cidr6={"2001:db8:1::/48", "2001:db8::/32"},
    )

    rules.filter(Option())

    assert rules.ip_cidr == {"1.1.1.0/24", "10.0.0.0/8"}
    assert rules.ip_cidr6 == {"2001:db8::/32"}


def test_serialization_orders_rule_fields():
    rules = RuleModel(
        domain={
            "b.example.com",
            "a.example.com",
            "z.example.net",
            "example.com",
            "az.example.com",
            "za.example.com",
        },
        domain_suffix={"suffix.example.com", "suffix.example.net"},
        domain_wildcard={"*.wild.example.net", "*.wild.example.com"},
        domain_regex={r"^b", r"^a"},
        domain_keyword={"b", "a"},
        ip_cidr={"10.1.0.0/16", "2.2.2.0/24", "1.1.1.0/24"},
        ip_cidr6={"2001:db9::/32", "2001:db8::/32"},
        ip_asn={"10", "2"},
        process={"z", "a"},
        user_agent={"b", "a"},
        url_regex={"b", "a"},
    )

    serializable = rules.to_serializable_rule_model()

    assert serializable.domain == [
        "example.com",
        "a.example.com",
        "az.example.com",
        "b.example.com",
        "za.example.com",
        "z.example.net",
    ]
    assert serializable.domain_suffix == [
        "suffix.example.com",
        "suffix.example.net",
    ]
    assert serializable.domain_wildcard == [
        "*.wild.example.com",
        "*.wild.example.net",
    ]
    assert serializable.domain_regex == [r"^a", r"^b"]
    assert serializable.domain_keyword == ["a", "b"]
    assert serializable.ip_cidr == ["1.1.1.0/24", "2.2.2.0/24", "10.1.0.0/16"]
    assert serializable.ip_cidr6 == ["2001:db8::/32", "2001:db9::/32"]
    assert serializable.ip_asn == ["2", "10"]
    assert serializable.process == ["a", "z"]
    assert serializable.user_agent == ["a", "b"]
    assert serializable.url_regex == ["a", "b"]


def test_serialization_orders_logical_rules_without_canonicalizing_children():
    b = _and("b", "d")
    c = _and("c", "a")

    serializable = RuleModel(logical={c, b}).to_serializable_rule_model()

    assert [_domain_values(tree) for tree in serializable.logical] == [
        ("b", "d"),
        ("c", "a"),
    ]


def test_to_serializable_rule_model_maps_all_rule_kinds():
    rules = RuleModel.model_validate(
        {
            "domain": {"b.example.com", "a.example.com"},
            "domain_suffix": {"example.net"},
            "domain_wildcard": {"*.example.org"},
            "domain_regex": {r"^b", r"^a"},
            "domain_keyword": {"b", "a"},
            "ip_cidr": {"2.2.2.0/24", "1.1.1.0/24"},
            "ip_cidr6": {"2001:db9::/32", "2001:db8::/32"},
            "ip_asn": {"10", "2"},
            "process": {"b", "a"},
            "user_agent": {"b", "a"},
            "url_regex": {"b", "a"},
        }
    )

    serializable = rules.to_serializable_rule_model()

    assert serializable.domain == ["a.example.com", "b.example.com"]
    assert serializable.domain_suffix == ["example.net"]
    assert serializable.domain_wildcard == ["*.example.org"]
    assert serializable.domain_regex == [r"^a", r"^b"]
    assert serializable.domain_keyword == ["a", "b"]
    assert serializable.ip_cidr == ["1.1.1.0/24", "2.2.2.0/24"]
    assert serializable.ip_cidr6 == ["2001:db8::/32", "2001:db9::/32"]
    assert serializable.ip_asn == ["2", "10"]
    assert serializable.process == ["a", "b"]
    assert serializable.user_agent == ["a", "b"]
    assert serializable.url_regex == ["a", "b"]
