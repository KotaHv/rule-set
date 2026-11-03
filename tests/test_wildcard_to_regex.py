import re

import pytest

from rule_set.utils.domain import wildcard_to_regex


@pytest.mark.parametrize(
    ("pattern", "expected"),
    [
        ("*.example.com", r"^.*\.example\.com$"),
        ("api?.example.com", r"^api.\.example\.com$"),
        ("ad[abc].example.com", r"^ad[abc]\.example\.com$"),
        ("ad[a-z].example.com", r"^ad[a-z]\.example\.com$"),
        ("ad[!a-z].example.com", r"^ad[^a-z]\.example\.com$"),
        ("ad[^a-z].example.com", r"^ad[^a-z]\.example\.com$"),
        ("a+b.example.com", r"^a\+b\.example\.com$"),
        ("a(b).example.com", r"^a\(b\)\.example\.com$"),
    ],
)
def test_translation(pattern, expected):
    """Output is fed to sing-box (RE2), so keep it plain and escaped."""
    assert wildcard_to_regex(pattern) == expected


@pytest.mark.parametrize(
    ("pattern", "host", "expected"),
    [
        ("*.example.com", "a.example.com", True),
        ("*.example.com", "a.b.example.com", True),
        ("*.example.com", "example.com", False),
        ("ads-*.tiktok.com", "ads-.tiktok.com", True),
        ("ads-*.tiktok.com", "ads-a.b.tiktok.com", True),
        ("api?.example.com", "apix.example.com", True),
        ("api?.example.com", "api.example.com", False),
        ("api?.example.com", "api12.example.com", False),
        ("ad[0-9].example.com", "ad1.example.com", True),
        ("ad[0-9].example.com", "adx.example.com", False),
        ("ad[0-9].example.com", "ad12.example.com", False),
        ("ad[!0-9].example.com", "adx.example.com", True),
        ("ad[!0-9].example.com", "ad1.example.com", False),
        ("ad[^0-9].example.com", "adx.example.com", True),
        ("ad[^0-9].example.com", "ad1.example.com", False),
        ("a+b.example.com", "a+b.example.com", True),
        ("a+b.example.com", "aaab.example.com", False),
        ("a(b).example.com", "a(b).example.com", True),
        ("a(b).example.com", "ab.example.com", False),
    ],
)
def test_matching(pattern, host, expected):
    regex = re.compile(wildcard_to_regex(pattern), re.IGNORECASE)
    assert bool(regex.fullmatch(host)) is expected
