from rule_set.models import Option, RuleModel


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
