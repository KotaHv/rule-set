import pytest

from rule_set.models import (
    DomainType,
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

DOMAIN = DomainType.DOMAIN
SUFFIX = DomainType.DOMAIN_SUFFIX
WILDCARD = DomainType.DOMAIN_WILDCARD


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
    rules = RuleModel(domain_regex={r"^ads\.", r"\.tracking\."})
    rules.domain_trie.add("ads.example.com", DomainType.DOMAIN)
    rules.domain_trie.add("www.tracking.example.com", DomainType.DOMAIN)
    rules.domain_trie.add("keep.example.com", DomainType.DOMAIN)
    rules.domain_trie.add("ads.example.net", DomainType.DOMAIN_SUFFIX)

    rules.filter(Option())

    assert sorted(rules.domain_trie.items()) == sorted(
        [
            ("keep.example.com", DomainType.DOMAIN),
            ("ads.example.net", DomainType.DOMAIN_SUFFIX),
        ]
    )


def test_invalid_domain_regex_does_not_break_filtering():
    rules = RuleModel(domain_regex={r"[invalid"})
    rules.domain_trie.add("ads.example.com", DomainType.DOMAIN)

    rules.filter(Option())

    assert rules.domain_trie.items() == [("ads.example.com", DomainType.DOMAIN)]


def test_merge_with_merges_rule_collections():
    rules = RuleModel.model_validate(
        {
            "domain_regex": {r"^a\."},
            "domain_keyword": {"ads"},
            "ip_trie": ["1.1.1.0/24"],
            "ip_trie6": ["2001:db8::/32"],
            "ip_asn": {"13335"},
            "process": {"first-process"},
            "user_agent": {"first-agent"},
            "url_regex": {"first-url"},
        }
    )
    rules.domain_trie.add("a.example.com", DOMAIN)
    other = RuleModel.model_validate(
        {
            "domain_regex": {r"^b\."},
            "domain_keyword": {"tracking"},
            "ip_trie": ["2.2.2.0/24"],
            "ip_trie6": ["2001:db9::/32"],
            "ip_asn": {"15169"},
            "process": {"second-process"},
            "user_agent": {"second-agent"},
            "url_regex": {"second-url"},
        }
    )
    other.domain_trie.add("b.example.com", DOMAIN)

    rules.merge_with(other)

    assert sorted(rules.domain_trie.items()) == sorted(
        [
            ("a.example.com", DOMAIN),
            ("b.example.com", DOMAIN),
        ]
    )
    assert rules.domain_regex == {r"^a\.", r"^b\."}
    assert rules.domain_keyword == {"ads", "tracking"}
    assert set(rules.ip_trie.iteritems()) == {"1.1.1.0/24", "2.2.2.0/24"}
    assert set(rules.ip_trie6.iteritems()) == {"2001:db8::/32", "2001:db9::/32"}
    assert rules.ip_asn == {"13335", "15169"}
    assert rules.process == {"first-process", "second-process"}
    assert rules.user_agent == {"first-agent", "second-agent"}
    assert rules.url_regex == {"first-url", "second-url"}


def _populated_rules() -> RuleModel:
    rules = RuleModel.model_validate(
        {
            "domain_regex": {r"^ads\."},
            "domain_keyword": {"tracking"},
            "ip_trie": ["1.1.1.0/24"],
            "ip_trie6": ["2001:db8::/32"],
            "ip_asn": {"13335"},
            "process": {"curl"},
            "user_agent": {"agent"},
            "url_regex": {"^https://"},
        }
    )
    rules.domain_trie.add("example.com", DOMAIN)
    rules.domain_trie.add("example.net", SUFFIX)
    rules.domain_trie.add("*.example.org", WILDCARD)
    rules.logical.add(_and("b", "d"))
    return rules


def _rule_type_state(rules: RuleModel) -> dict[ProcessingRuleType, list[str]]:
    domains: dict[DomainType, list[str]] = {
        domain_type: [] for domain_type in DomainType
    }
    for domain, domain_type in rules.domain_trie.items():
        domains[domain_type].append(domain)
    return {
        ProcessingRuleType.DOMAIN: sorted(domains[DomainType.DOMAIN]),
        ProcessingRuleType.DOMAIN_SUFFIX: sorted(domains[DomainType.DOMAIN_SUFFIX]),
        ProcessingRuleType.DOMAIN_WILDCARD: sorted(domains[DomainType.DOMAIN_WILDCARD]),
        ProcessingRuleType.DOMAIN_REGEX: sorted(rules.domain_regex),
        ProcessingRuleType.DOMAIN_KEYWORD: sorted(rules.domain_keyword),
        ProcessingRuleType.IP_CIDR: sorted(rules.ip_trie.iteritems()),
        ProcessingRuleType.IP_CIDR6: sorted(rules.ip_trie6.iteritems()),
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

    assert rules.domain_trie.items() == [("example.net", SUFFIX)]
    assert set(rules.ip_trie.iteritems()) == {"1.1.1.0/24"}
    assert list(rules.ip_trie6.iteritems()) == []
    assert rules.domain_regex == set()
    assert rules.domain_keyword == set()
    assert rules.ip_asn == set()
    assert rules.logical == set()
    assert rules.process == set()
    assert rules.user_agent == set()
    assert rules.url_regex == set()


def test_filter_excludes_suffixes():
    rules = RuleModel()
    rules.domain_trie.add("example.com", SUFFIX)
    rules.domain_trie.add("example.net", DOMAIN)

    rules.filter(
        Option(
            processing=ProcessingOption(
                exclude_suffixes=["example.com", "missing.example"]
            )
        )
    )

    assert rules.domain_trie.items() == [("example.net", DOMAIN)]


def test_filter_deduplicates_domain_keywords():
    rules = RuleModel(domain_keyword={"ads", "ads.example.com", "tracking"})

    rules.filter(Option())

    assert rules.domain_keyword == {"ads", "tracking"}


def test_filter_applies_keywords_to_trie_and_regex():
    rules = RuleModel(domain_regex={r"^ads\.example\.com$", r"^keep\.example\.com$"})
    rules.domain_trie.add("ads.example.net", DOMAIN)
    rules.domain_trie.add("keep.example.net", DOMAIN)

    rules.filter(Option(processing=ProcessingOption(exclude_keywords=["ads"])))

    assert rules.domain_trie.items() == [("keep.example.net", DOMAIN)]
    assert rules.domain_regex == {r"^keep\.example\.com$"}


def test_serialization_orders_rule_fields():
    rules = RuleModel(
        domain_regex={r"^b", r"^a"},
        domain_keyword={"b", "a"},
        ip_asn={"10", "2"},
        process={"z", "a"},
        user_agent={"b", "a"},
        url_regex={"b", "a"},
    )

    serializable = rules.to_serializable_rule_model()

    assert serializable.domain_regex == [r"^a", r"^b"]
    assert serializable.domain_keyword == ["a", "b"]
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
            "domain_regex": {r"^b", r"^a"},
            "domain_keyword": {"b", "a"},
            "ip_trie": ["2.2.2.0/24", "1.1.1.0/24"],
            "ip_trie6": ["2001:db9::/32", "2001:db8::/32"],
            "ip_asn": {"10", "2"},
            "process": {"b", "a"},
            "user_agent": {"b", "a"},
            "url_regex": {"b", "a"},
        }
    )
    rules.domain_trie.add("b.example.com", DOMAIN)
    rules.domain_trie.add("a.example.com", DOMAIN)
    rules.domain_trie.add("example.net", SUFFIX)
    rules.domain_trie.add("*.example.org", WILDCARD)

    serializable = rules.to_serializable_rule_model()

    assert serializable.domain == ["a.example.com", "b.example.com"]
    assert serializable.domain_suffix == ["example.net"]
    assert serializable.domain_wildcard == ["*.example.org"]
    assert serializable.domain_regex == [r"^a", r"^b"]
    assert set(serializable.domain_keyword) == {"a", "b"}
    assert set(serializable.ip_cidr) == {"1.1.1.0/24", "2.2.2.0/24"}
    assert set(serializable.ip_cidr6) == {"2001:db8::/32", "2001:db9::/32"}
    assert set(serializable.ip_asn) == {"2", "10"}
    assert set(serializable.process) == {"a", "b"}
    assert set(serializable.user_agent) == {"a", "b"}
    assert set(serializable.url_regex) == {"a", "b"}
