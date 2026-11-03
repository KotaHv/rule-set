import pytest

from rule_set.utils.domain import regex_to_wildcard


@pytest.mark.parametrize(
    ("domain_regex", "expected"),
    [
        (
            r".+\.awsdns-[0-9][0-9]\.(co\.uk|com|net|org)$",
            ["*.awsdns-[0-9][0-9].*"],
        ),
        (
            r".+\.awsdns-cn-[0-9][0-9]\.(biz|com|net|top)$",
            ["*.awsdns-cn-[0-9][0-9].*"],
        ),
        (r".+\.dkr\.ecr\.[^\.]+\.amazonaws\.com$", ["*.dkr.ecr.*.amazonaws.com"]),
        (r"^.+-mihayo\.akamaized\.net$", ["*-mihayo.akamaized.net"]),
        (
            r"^epicgames-download\d\.akamaized\.net$",
            ["epicgames-download[0-9].akamaized.net"],
        ),
    ],
)
def test_existing_rules(domain_regex, expected):
    assert regex_to_wildcard(domain_regex) == expected


@pytest.mark.parametrize(
    ("domain_regex", "expected"),
    [
        (r"^[abce]\.example\.com$", ["[abce].example.com"]),
        (r"^[a-z]\.example\.com$", ["[a-z].example.com"]),
        (r"^[0-9][a-z]\.example\.com$", ["[0-9][a-z].example.com"]),
        (r"^[^a]\.example\.com$", ["[!a].example.com"]),
        (r"^[^\.]\.example\.com$", ["[!.].example.com"]),
        (r"^x[\d]b\.com$", ["x[0-9]b.com"]),
        (r"^x[\w]b\.com$", ["x?b.com"]),
    ],
)
def test_character_class(domain_regex, expected):
    assert regex_to_wildcard(domain_regex) == expected


@pytest.mark.parametrize(
    ("domain_regex", "expected"),
    [
        (
            r"^[a-z]{2,3}\.example\.com$",
            ["[a-z][a-z].example.com", "[a-z][a-z][a-z].example.com"],
        ),
        (r"^[a-z]{3}\.example\.com$", ["[a-z][a-z][a-z].example.com"]),
        # Unbounded or too wide to expand: a wildcard can only say "anything".
        (r"^[a-z]{2,8}\.example\.com$", ["*.example.com"]),
        (r"^[a-z]+\.[abc]+\.example\.com$", ["*.*.example.com"]),
        (r"^a+\.com$", ["*.com"]),
        (r"^a{3,}\.com$", ["*.com"]),
    ],
)
def test_repetition(domain_regex, expected):
    assert regex_to_wildcard(domain_regex) == expected
