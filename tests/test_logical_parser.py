import pytest

from rule_set.models.logical import AndNode, NotNode, OrNode, RuleNode
from rule_set.parsers.logic import parse


def test_parse_nested_operators_and_parent_links():
    tree = parse(
        "AND,((DOMAIN-SUFFIX,example.com),"
        "(OR,((IP-CIDR,192.0.2.0/24,no-resolve),"
        "(NOT,((DOMAIN-KEYWORD,ads))))))"
    )

    assert tree is not None
    assert isinstance(tree.root, AndNode)
    assert isinstance(tree.root.children[0], RuleNode)
    assert tree.root.children[0].rule.rule_values == ("example.com",)

    nested = tree.root.children[1]
    assert isinstance(nested, OrNode)
    assert nested.parent is tree.root
    assert isinstance(nested.children[0], RuleNode)
    assert nested.children[0].rule.rule_values == ("192.0.2.0/24", "no-resolve")

    negated = nested.children[1]
    assert isinstance(negated, NotNode)
    assert negated.parent is nested
    assert isinstance(negated.child, RuleNode)
    assert negated.child.rule.rule_values == ("ads",)


@pytest.mark.parametrize(
    "rule",
    [
        "AND,((DOMAIN-SUFFIX,example.com))",
        "NOT,((DOMAIN-SUFFIX,example.com),(DOMAIN-KEYWORD,ads))",
        "AND,((UNKNOWN,example.com),(DOMAIN-SUFFIX,example.com))",
    ],
)
def test_parse_invalid_logical_rules_returns_none(rule):
    assert parse(rule) is None
