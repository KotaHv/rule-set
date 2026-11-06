import pytest

from rule_set.models.logical import (
    ConcreteRule,
    Logical,
    LogicalOperator,
    LogicalTree,
    Node,
    Rule,
    RuleType,
)


def _rule(rule_type: RuleType, *values: str) -> Rule:
    return Rule(rule=ConcreteRule(rule_type=rule_type, rule_values=values))


def _logical(op: LogicalOperator, *children: Node) -> Logical:
    return Logical(op=op, children=children)


@pytest.mark.parametrize("op", [LogicalOperator.AND, LogicalOperator.OR])
def test_logical_tree_equality_ignores_child_order_and_associativity(op):
    a = _rule(RuleType.DOMAIN, "a")
    b = _rule(RuleType.DOMAIN, "b")
    c = _rule(RuleType.DOMAIN, "c")

    first = LogicalTree(root=_logical(op, a, b))
    reversed_first = LogicalTree(root=_logical(op, b, a))
    flat = LogicalTree(root=_logical(op, a, b, c))
    left_nested = LogicalTree(root=_logical(op, _logical(op, a, b), c))
    right_nested = LogicalTree(root=_logical(op, a, _logical(op, b, c)))

    assert first == reversed_first
    assert flat == left_nested
    assert flat == right_nested
    assert len({first, reversed_first}) == 1
    assert len({flat, left_nested, right_nested}) == 1


def test_logical_tree_equality_keeps_rule_value_order():
    first = LogicalTree(
        root=_logical(
            LogicalOperator.AND,
            _rule(RuleType.IP_CIDR, "192.0.2.0/24", "no-resolve"),
            _rule(RuleType.DOMAIN, "example.com"),
        )
    )
    second = LogicalTree(
        root=_logical(
            LogicalOperator.AND,
            _rule(RuleType.IP_CIDR, "no-resolve", "192.0.2.0/24"),
            _rule(RuleType.DOMAIN, "example.com"),
        )
    )

    assert first != second


def test_logical_tree_ordering_uses_canonical_key():
    b = LogicalTree(
        root=_logical(
            LogicalOperator.AND,
            _rule(RuleType.DOMAIN, "b"),
            _rule(RuleType.DOMAIN, "d"),
        )
    )
    c = LogicalTree(
        root=_logical(
            LogicalOperator.AND,
            _rule(RuleType.DOMAIN, "c"),
            _rule(RuleType.DOMAIN, "a"),
        )
    )

    assert c < b
