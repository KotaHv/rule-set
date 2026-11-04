import pytest
from pydantic import TypeAdapter

from rule_set.models.trie import IPTrie, IPTrie6

LARGE_V4_PREFIXES = [
    "10.0.0.0/8",
    "10.1.0.0/16",
    "10.1.1.0/24",
    "10.1.1.1/32",
    "10.2.0.0/16",
    "172.16.0.0/12",
    "172.16.1.0/24",
    "172.16.1.0/24",
    "192.168.0.0/16",
    "192.168.1.0/24",
    "192.168.2.0/24",
    "1.1.1.0/24",
    "2.2.2.0/24",
    "8.8.8.8/32",
    "100.64.0.0/10",
    "100.64.1.0/24",
    "203.0.113.0/24",
]
LARGE_V4_EXPECTED = {
    "1.1.1.0/24",
    "10.0.0.0/8",
    "100.64.0.0/10",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "2.2.2.0/24",
    "203.0.113.0/24",
    "8.8.8.8/32",
}

LARGE_V6_PREFIXES = [
    "2001:db8::/32",
    "2001:db8:1::/48",
    "2001:db8:1:1::/64",
    "2001:db8:1:1::1/128",
    "2001:db8:2::/48",
    "2001:db9::/32",
    "2001:db9:1::/48",
    "2001:db9:2::/48",
    "2606:4700::/32",
    "2606:4700:1::/48",
    "2a00:1450::/32",
    "2a03:2880::/32",
    "fe80::/10",
    "::1/128",
    "2001:db8:3::/48",
]
LARGE_V6_EXPECTED = {
    "2001:db8::/32",
    "2001:db9::/32",
    "2606:4700::/32",
    "2a00:1450::/32",
    "2a03:2880::/32",
    "::1/128",
    "fe80::/10",
}

ADD_CASES = [
    pytest.param(IPTrie, [], set(), id="v4-empty"),
    pytest.param(IPTrie, ["10.0.0.0/8"], {"10.0.0.0/8"}, id="v4-single"),
    pytest.param(
        IPTrie,
        ["10.0.0.0/8", "10.1.0.0/16"],
        {"10.0.0.0/8"},
        id="v4-parent-first",
    ),
    pytest.param(
        IPTrie,
        ["10.1.0.0/16", "10.0.0.0/8"],
        {"10.0.0.0/8"},
        id="v4-parent-last",
    ),
    pytest.param(
        IPTrie,
        ["10.0.0.0/8", "10.0.0.0/8"],
        {"10.0.0.0/8"},
        id="v4-duplicate",
    ),
    pytest.param(
        IPTrie,
        ["10.0.0.0/8", "10.1.0.0/16", "10.1.1.0/24", "10.2.0.0/16"],
        {"10.0.0.0/8"},
        id="v4-multi-level-parent-first",
    ),
    pytest.param(
        IPTrie,
        ["10.1.0.0/16", "10.2.0.0/16", "10.0.0.0/8"],
        {"10.0.0.0/8"},
        id="v4-multi-level-parent-last",
    ),
    pytest.param(
        IPTrie,
        ["1.1.1.0/24", "1.1.1.1/32"],
        {"1.1.1.0/24"},
        id="v4-host-covered-by-network",
    ),
    pytest.param(
        IPTrie,
        ["1.1.1.1/32", "1.1.1.0/24"],
        {"1.1.1.0/24"},
        id="v4-network-covers-host",
    ),
    pytest.param(
        IPTrie,
        ["1.1.1.0/24", "2.2.2.0/24"],
        {"1.1.1.0/24", "2.2.2.0/24"},
        id="v4-independent",
    ),
    pytest.param(
        IPTrie,
        ["10.1.0.0/16", "10.2.0.0/16"],
        {"10.1.0.0/16", "10.2.0.0/16"},
        id="v4-siblings",
    ),
    pytest.param(
        IPTrie,
        ["0.0.0.0/0", "10.0.0.0/8", "192.168.0.0/16"],
        {"0.0.0.0/0"},
        id="v4-default-route",
    ),
    pytest.param(IPTrie6, [], set(), id="v6-empty"),
    pytest.param(IPTrie6, ["2001:db8::/32"], {"2001:db8::/32"}, id="v6-single"),
    pytest.param(
        IPTrie6,
        ["2001:db8::/32", "2001:db8:1::/48"],
        {"2001:db8::/32"},
        id="v6-parent-first",
    ),
    pytest.param(
        IPTrie6,
        ["2001:db8:1::/48", "2001:db8::/32"],
        {"2001:db8::/32"},
        id="v6-parent-last",
    ),
    pytest.param(
        IPTrie6,
        ["2001:db8:1::/48", "2001:db8:1::1/128"],
        {"2001:db8:1::/48"},
        id="v6-host-covered-by-network",
    ),
    pytest.param(
        IPTrie6,
        ["2001:db8:1::1/128", "2001:db8:1::/48"],
        {"2001:db8:1::/48"},
        id="v6-network-covers-host",
    ),
    pytest.param(
        IPTrie6,
        ["2001:db8:1::/48", "2001:db8:2::/48"],
        {"2001:db8:1::/48", "2001:db8:2::/48"},
        id="v6-independent",
    ),
    pytest.param(
        IPTrie6,
        ["2001:db8::/32", "2001:db9::/32"],
        {"2001:db8::/32", "2001:db9::/32"},
        id="v6-independent-32s",
    ),
    pytest.param(
        IPTrie6,
        ["::/0", "2001:db8::/32"],
        {"::/0"},
        id="v6-default-route",
    ),
    pytest.param(
        IPTrie,
        LARGE_V4_PREFIXES,
        LARGE_V4_EXPECTED,
        id="v4-large",
    ),
    pytest.param(
        IPTrie6,
        LARGE_V6_PREFIXES,
        LARGE_V6_EXPECTED,
        id="v6-large",
    ),
]

MERGE_CASES = [
    pytest.param(
        IPTrie,
        ["10.1.0.0/16"],
        ["10.0.0.0/8"],
        {"10.0.0.0/8"},
        id="v4-right-parent",
    ),
    pytest.param(
        IPTrie,
        ["10.0.0.0/8"],
        ["10.1.0.0/16"],
        {"10.0.0.0/8"},
        id="v4-left-parent",
    ),
    pytest.param(
        IPTrie,
        ["10.1.0.0/16"],
        ["10.2.0.0/16"],
        {"10.1.0.0/16", "10.2.0.0/16"},
        id="v4-siblings",
    ),
    pytest.param(
        IPTrie,
        ["10.0.0.0/8"],
        ["192.168.0.0/16"],
        {"10.0.0.0/8", "192.168.0.0/16"},
        id="v4-independent",
    ),
    pytest.param(
        IPTrie6,
        ["2001:db8:1::/48"],
        ["2001:db8::/32"],
        {"2001:db8::/32"},
        id="v6-right-parent",
    ),
    pytest.param(
        IPTrie6,
        ["2001:db8::/32"],
        ["2001:db8:1::/48"],
        {"2001:db8::/32"},
        id="v6-left-parent",
    ),
    pytest.param(
        IPTrie6,
        ["2001:db8::/32"],
        ["2001:db9::/32"],
        {"2001:db8::/32", "2001:db9::/32"},
        id="v6-independent",
    ),
    pytest.param(
        IPTrie,
        LARGE_V4_PREFIXES[:8],
        LARGE_V4_PREFIXES[8:],
        LARGE_V4_EXPECTED,
        id="v4-large",
    ),
    pytest.param(
        IPTrie6,
        LARGE_V6_PREFIXES[:7],
        LARGE_V6_PREFIXES[7:],
        LARGE_V6_EXPECTED,
        id="v6-large",
    ),
]

ROUND_TRIP_CASES = [
    pytest.param(IPTrie, [], set(), id="v4-empty"),
    pytest.param(
        IPTrie,
        ["1.1.1.0/24", "2.2.2.0/24"],
        {"1.1.1.0/24", "2.2.2.0/24"},
        id="v4-independent",
    ),
    pytest.param(
        IPTrie,
        ["10.1.0.0/16", "10.0.0.0/8"],
        {"10.0.0.0/8"},
        id="v4-overlap",
    ),
    pytest.param(IPTrie6, [], set(), id="v6-empty"),
    pytest.param(
        IPTrie6,
        ["2001:db8:1::/48", "2001:db8::/32"],
        {"2001:db8::/32"},
        id="v6-overlap",
    ),
    pytest.param(
        IPTrie6,
        ["2001:db8::/32", "2001:db9::/32"],
        {"2001:db8::/32", "2001:db9::/32"},
        id="v6-independent",
    ),
    pytest.param(
        IPTrie,
        LARGE_V4_PREFIXES,
        LARGE_V4_EXPECTED,
        id="v4-large",
    ),
    pytest.param(
        IPTrie6,
        LARGE_V6_PREFIXES,
        LARGE_V6_EXPECTED,
        id="v6-large",
    ),
]


@pytest.mark.parametrize(("trie_type", "prefixes", "expected"), ADD_CASES)
def test_add_prefixes(trie_type, prefixes, expected):
    trie = trie_type()
    for prefix in prefixes:
        trie.add(prefix)

    assert set(trie.iteritems()) == expected


@pytest.mark.parametrize(("trie_type", "left", "right", "expected"), MERGE_CASES)
def test_merge_keeps_parent_prefix(trie_type, left, right, expected):
    trie = trie_type()
    for prefix in left:
        trie.add(prefix)
    other = trie_type()
    for prefix in right:
        other.add(prefix)

    trie.merge(other)

    assert set(trie.iteritems()) == expected


@pytest.mark.parametrize(("trie_type", "prefixes", "expected"), ROUND_TRIP_CASES)
def test_pydantic_schema_round_trip(trie_type, prefixes, expected):
    adapter = TypeAdapter(trie_type)
    trie = adapter.validate_python(prefixes)

    assert set(trie.iteritems()) == expected
    assert set(adapter.dump_python(trie)) == expected
