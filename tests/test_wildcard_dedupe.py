import pytest

from rule_set.models.enum import DomainType
from rule_set.models.trie import DomainTrie

DOMAIN = DomainType.DOMAIN
SUFFIX = DomainType.DOMAIN_SUFFIX
WILDCARD = DomainType.DOMAIN_WILDCARD
REGEX = DomainType.DOMAIN_REGEX


@pytest.mark.parametrize(
    ("rules", "expected"),
    [
        # DOMAIN covered by a wildcard
        (
            [("bar.foo.com", DOMAIN), ("*.foo.com", WILDCARD)],
            [("*.foo.com", WILDCARD)],
        ),
        # insertion order must not matter
        (
            [("*.foo.com", WILDCARD), ("bar.foo.com", DOMAIN)],
            [("*.foo.com", WILDCARD)],
        ),
        (
            [
                ("upos-sz-mirrorali*.bilivideo.com", WILDCARD),
                ("upos-sz-mirrorali01.bilivideo.com", DOMAIN),
            ],
            [("upos-sz-mirrorali*.bilivideo.com", WILDCARD)],
        ),
        (
            [
                ("foo*bar.baz.com", WILDCARD),
                ("foo.xbar.baz.com", DOMAIN),
            ],
            [("foo*bar.baz.com", WILDCARD)],
        ),
        (
            [
                ("api?.example.com", WILDCARD),
                ("apix.example.com", DOMAIN),
                ("api.example.com", DOMAIN),
            ],
            [("api?.example.com", WILDCARD), ("api.example.com", DOMAIN)],
        ),
        (
            [
                ("ad[0-9].example.com", WILDCARD),
                ("ad1.example.com", DOMAIN),
                ("adx.example.com", DOMAIN),
            ],
            [("ad[0-9].example.com", WILDCARD), ("adx.example.com", DOMAIN)],
        ),
        # DOMAIN not covered
        (
            [("*.foo.com", WILDCARD), ("foo.com", DOMAIN)],
            [("*.foo.com", WILDCARD), ("foo.com", DOMAIN)],
        ),
        (
            [
                ("upos-sz-mirrorali*.bilivideo.com", WILDCARD),
                ("a.upos-sz-mirrorali.bilivideo.com", DOMAIN),
            ],
            [
                ("upos-sz-mirrorali*.bilivideo.com", WILDCARD),
                ("a.upos-sz-mirrorali.bilivideo.com", DOMAIN),
            ],
        ),
        (
            [
                ("example.c*", WILDCARD),
                ("service.*", WILDCARD),
                ("example.com", DOMAIN),
                ("example.co.uk", DOMAIN),
                ("example.org", DOMAIN),
                ("service.net", DOMAIN),
                ("cdn.example.com", DOMAIN),
            ],
            [
                ("example.c*", WILDCARD),
                ("service.*", WILDCARD),
                ("example.org", DOMAIN),
                ("cdn.example.com", DOMAIN),
            ],
        ),
        (
            [("example.c*", WILDCARD), ("example.com", SUFFIX)],
            [("example.c*", WILDCARD), ("example.com", SUFFIX)],
        ),
        # DOMAIN-SUFFIX covered by a wildcard with a leading "*"
        (
            [("*.foo.com", WILDCARD), ("bar.foo.com", SUFFIX)],
            [("*.foo.com", WILDCARD)],
        ),
        # a wildcard without a leading "*" only matches the apex, not its subdomains
        (
            [("ads-*.tiktok.com", WILDCARD), ("ads-api.tiktok.com", SUFFIX)],
            [("ads-*.tiktok.com", WILDCARD), ("ads-api.tiktok.com", SUFFIX)],
        ),
        (
            [("ftp.??.debian.org", WILDCARD), ("ftp.au.debian.org", SUFFIX)],
            [("ftp.??.debian.org", WILDCARD), ("ftp.au.debian.org", SUFFIX)],
        ),
        # only the matching suffix is removed
        (
            [
                ("*.foo.com", WILDCARD),
                ("bar.foo.com", SUFFIX),
                ("keep.com", SUFFIX),
            ],
            [("*.foo.com", WILDCARD), ("keep.com", SUFFIX)],
        ),
        # other rule types are left alone
        (
            [
                ("^ads\\.foo\\.com$", REGEX),
                ("*.foo.com", WILDCARD),
                ("keep.com", DOMAIN),
            ],
            [
                ("^ads\\.foo\\.com$", REGEX),
                ("*.foo.com", WILDCARD),
                ("keep.com", DOMAIN),
            ],
        ),
        # only the matching wildcard is used
        (
            [
                ("a*.foo.com", WILDCARD),
                ("b*.foo.com", WILDCARD),
                ("b1.foo.com", DOMAIN),
            ],
            [("a*.foo.com", WILDCARD), ("b*.foo.com", WILDCARD)],
        ),
        # no wildcard at all
        (
            [("a.foo.com", DOMAIN), ("b.bar.com", DOMAIN)],
            [("a.foo.com", DOMAIN), ("b.bar.com", DOMAIN)],
        ),
    ],
)
def test_dedupe(rules, expected):
    trie = DomainTrie()
    for domain, domain_type in rules:
        trie.add(domain, domain_type)
    trie.filter_by_wildcard()
    assert sorted(trie.items()) == sorted(expected)
