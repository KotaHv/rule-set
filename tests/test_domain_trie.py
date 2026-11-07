from pydantic import TypeAdapter

from rule_set.models import DomainType
from rule_set.models.trie import DomainTrie

DOMAIN = DomainType.DOMAIN
SUFFIX = DomainType.DOMAIN_SUFFIX
WILDCARD = DomainType.DOMAIN_WILDCARD


def test_add_suffix_clears_and_blocks_children():
    trie = DomainTrie()
    trie.add("ads.example.com", DOMAIN)
    trie.add("example.com", SUFFIX)
    trie.add("www.example.com", DOMAIN)

    assert trie.items() == [("example.com", SUFFIX)]


def test_remove_only_removes_requested_domain():
    trie = DomainTrie()
    trie.add("ads.example.com", DOMAIN)
    trie.add("cdn.example.com", DOMAIN)

    trie.remove("ads.example.com")
    trie.remove("missing.example.com")

    assert trie.items() == [("cdn.example.com", DOMAIN)]


def test_merge_keeps_suffix_precedence():
    trie = DomainTrie()
    trie.add("ads.example.com", DOMAIN)
    other = DomainTrie()
    other.add("example.com", SUFFIX)

    trie.merge(other)

    assert trie.items() == [("example.com", SUFFIX)]


def test_sorted_iteritems_orders_by_reversed_labels():
    trie = DomainTrie()
    trie.add("b.example.com", DOMAIN)
    trie.add("a.example.com", DOMAIN)
    trie.add("z.net", DOMAIN)

    assert [domain for domain, _ in trie.sorted_iteritems()] == [
        "a.example.com",
        "b.example.com",
        "z.net",
    ]


def test_pydantic_schema_round_trip():
    adapter = TypeAdapter(DomainTrie)
    trie = adapter.validate_python(
        {
            DOMAIN: ["b.com", "a.com"],
            SUFFIX: ["example.net"],
            WILDCARD: ["*.example.org"],
        }
    )

    assert sorted(trie.items()) == sorted(
        [
            ("a.com", DOMAIN),
            ("b.com", DOMAIN),
            ("example.net", SUFFIX),
            ("*.example.org", WILDCARD),
        ]
    )
    assert {
        domain_type: sorted(domains)
        for domain_type, domains in adapter.dump_python(trie).items()
    } == {
        DOMAIN: ["a.com", "b.com"],
        SUFFIX: ["example.net"],
        WILDCARD: ["*.example.org"],
    }


def test_pydantic_deserialized_trie_dedupes_wildcards():
    adapter = TypeAdapter(DomainTrie)
    trie = adapter.validate_python(
        {
            DOMAIN: ["bar.foo.com"],
            WILDCARD: ["*.foo.com"],
        }
    )

    trie.filter_by_wildcard()

    assert trie.items() == [("*.foo.com", WILDCARD)]
