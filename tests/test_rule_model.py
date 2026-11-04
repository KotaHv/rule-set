from rule_set.models import DomainType, Option, RuleModel


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
