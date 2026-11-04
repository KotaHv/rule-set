from rule_set.models import (
    Option,
    RuleModel,
    V2rayDomainAttrs,
    V2rayDomainOption,
)
from rule_set.parsers.v2ray_domain import parse


def test_v2ray_regex_is_stored_separately_and_serialized():
    option = V2rayDomainOption(
        attrs=V2rayDomainAttrs(),
        exclude_includes=[],
    )
    result = parse(r"regexp:^ads\.example\.com$", option)

    assert result.rules.domain_trie.items() == []
    assert result.rules.domain_regex == {r"^ads\.example\.com$"}
    assert result.rules.to_serializable_rule_model().domain_regex == [
        r"^ads\.example\.com$"
    ]


def test_domain_regex_merges_and_keyword_filtering_still_applies():
    rules = RuleModel(
        domain_regex={
            r"^ads\.example\.com$",
            r"^www\.bitiba\.com$",
            r"^cdn-txtagstore\.net$",
        }
    )
    rules.merge_with(RuleModel(domain_regex={r"^tracking\.example\.com$"}))

    rules.domain_keyword.update({"ads", ".bitiba.", "-txtagstore"})
    rules.filter(Option())

    assert rules.domain_regex == {r"^tracking\.example\.com$"}
