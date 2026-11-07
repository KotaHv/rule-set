import pytest

from rule_set.models.logical import Logical, LogicalOperator, Rule
from rule_set.parsers.logic import parse


def test_parse_nested_operators():
    tree = parse(
        "AND,((DOMAIN-SUFFIX,example.com),(OR,((IP-CIDR,192.0.2.0/24,no-resolve),(NOT,((DOMAIN-KEYWORD,ads))))))"
    )

    assert tree is not None
    assert tree.root.op is LogicalOperator.AND
    assert isinstance(tree.root.children[0], Rule)
    assert tree.root.children[0].rule.rule_values == ("example.com",)

    nested = tree.root.children[1]
    assert isinstance(nested, Logical)
    assert nested.op is LogicalOperator.OR
    assert isinstance(nested.children[0], Rule)
    assert nested.children[0].rule.rule_values == ("192.0.2.0/24", "no-resolve")

    negated = nested.children[1]
    assert isinstance(negated, Logical)
    assert negated.op is LogicalOperator.NOT
    assert isinstance(negated.children[0], Rule)
    assert negated.children[0].rule.rule_values == ("ads",)


@pytest.mark.parametrize(
    "rule",
    [
        "AND,((DOMAIN-SUFFIX,example.com))",
        "NOT,((DOMAIN-SUFFIX,example.com),(DOMAIN-KEYWORD,ads))",
        "AND,((UNKNOWN,example.com),(DOMAIN-SUFFIX,example.com))",
        "AND,((AND),(DOMAIN-SUFFIX,example.com))",
        "AND,((NOT),(DOMAIN-SUFFIX,example.com))",
    ],
)
def test_parse_invalid_logical_rules_returns_none(rule):
    assert parse(rule) is None
