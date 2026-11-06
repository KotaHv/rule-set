import yaml

from rule_set.models.logical import (
    ConcreteRule,
    Logical,
    LogicalOperator,
    LogicalTree,
    Node,
    Rule,
    RuleType,
)
from rule_set.models.option import Option
from rule_set.models.rule import SerializableRuleModel
from rule_set.serializers.clients.egern import EgernSerializer
from rule_set.serializers.logic.clash import serialize as serialize_clash
from rule_set.serializers.logic.sing_box import serialize as serialize_sing_box
from rule_set.serializers.logic.surge import serialize as serialize_surge


def _rule(rule_type: RuleType, *values: str) -> Rule:
    return Rule(rule=ConcreteRule(rule_type=rule_type, rule_values=values))


def _logical(op: LogicalOperator, *children: Node) -> Logical:
    return Logical(op=op, children=children)


def test_surge_serializes_nested_logical_rules():
    tree = LogicalTree(
        root=_logical(
            LogicalOperator.AND,
            _rule(RuleType.DOMAIN_SUFFIX, "example.com"),
            _logical(
                LogicalOperator.OR,
                _rule(RuleType.IP_CIDR, "192.0.2.0/24", "no-resolve"),
                _logical(
                    LogicalOperator.NOT,
                    _rule(RuleType.DOMAIN_KEYWORD, "ads"),
                ),
            ),
        )
    )

    assert serialize_surge(tree=tree) == (
        "AND,((DOMAIN-SUFFIX,example.com),"
        "(OR,((IP-CIDR,192.0.2.0/24,no-resolve),"
        "(NOT,((DOMAIN-KEYWORD,ads))))))"
    )


def test_clash_maps_logical_rule_aliases():
    tree = LogicalTree(
        root=_logical(
            LogicalOperator.OR,
            _rule(RuleType.PROTOCOL, "udp"),
            _rule(RuleType.DEST_PORT, "443"),
        )
    )

    assert serialize_clash(tree=tree) == "OR,((NETWORK,udp),(DST-PORT,443))"


class EgernTestLoader(yaml.SafeLoader):
    pass


def _construct_tagged_mapping(loader, tag_suffix, node):
    return f"!{tag_suffix}", loader.construct_mapping(node)


EgernTestLoader.add_multi_constructor("!", _construct_tagged_mapping)


def _serialize_egern_rules(logical: list[LogicalTree]) -> dict:
    serializer = EgernSerializer(
        rules=SerializableRuleModel(logical=logical),
        option=Option(serialization={"no_resolve": False}),
    )
    return yaml.load(serializer.serialize()[0].data, Loader=EgernTestLoader)


def test_egern_serializes_and_rule_sets_as_condition_groups():
    logical = [
        LogicalTree(
            root=_logical(
                LogicalOperator.AND,
                _rule(RuleType.IP_CIDR, "192.0.2.0/24", "no-resolve"),
                _rule(RuleType.DOMAIN_SUFFIX, "googlevideo.com"),
            )
        ),
        LogicalTree(
            root=_logical(
                LogicalOperator.AND,
                _rule(RuleType.IP_CIDR, "192.0.2.0/24", "no-resolve"),
                _logical(
                    LogicalOperator.NOT,
                    _rule(RuleType.DOMAIN_SUFFIX, "example.com"),
                ),
            )
        ),
    ]

    data = _serialize_egern_rules(logical)

    assert data["no_resolve"] is False
    assert data["and_set"] == [
        [
            ("!ip_cidr", {"match": "192.0.2.0/24", "no_resolve": True}),
            ("!domain_suffix", {"match": "googlevideo.com"}),
        ],
        [
            ("!ip_cidr", {"match": "192.0.2.0/24", "no_resolve": True}),
            ("!not", {"match": ("!domain_suffix", {"match": "example.com"})}),
        ],
    ]


def test_egern_serializes_multiple_standalone_not_rules():
    logical = [
        LogicalTree(
            root=_logical(
                LogicalOperator.NOT,
                _rule(RuleType.PROTOCOL, "UDP"),
            )
        ),
        LogicalTree(
            root=_logical(
                LogicalOperator.NOT,
                _rule(RuleType.DOMAIN_WILDCARD, "p2p*.qq.com"),
            )
        ),
        LogicalTree(
            root=_logical(
                LogicalOperator.NOT,
                _rule(RuleType.DOMAIN_SUFFIX, "example.com"),
            )
        ),
        LogicalTree(
            root=_logical(
                LogicalOperator.NOT,
                _rule(RuleType.DOMAIN_KEYWORD, "ads"),
            )
        ),
        LogicalTree(
            root=_logical(
                LogicalOperator.NOT,
                _logical(
                    LogicalOperator.AND,
                    _rule(RuleType.DOMAIN_SUFFIX, "example.com"),
                    _rule(RuleType.DOMAIN_KEYWORD, "ads"),
                ),
            )
        ),
        LogicalTree(
            root=_logical(
                LogicalOperator.NOT,
                _logical(
                    LogicalOperator.NOT,
                    _rule(RuleType.DOMAIN_SUFFIX, "example.com"),
                ),
            )
        ),
    ]

    data = _serialize_egern_rules(logical)

    assert data["not_set"] == [
        ("!protocol", {"match": "UDP"}),
        ("!domain_wildcard", {"match": "p2p*.qq.com"}),
        ("!domain_suffix", {"match": "example.com"}),
        ("!domain_keyword", {"match": "ads"}),
        (
            "!and",
            {
                "match": [
                    ("!domain_suffix", {"match": "example.com"}),
                    ("!domain_keyword", {"match": "ads"}),
                ]
            },
        ),
        ("!not", {"match": ("!domain_suffix", {"match": "example.com"})}),
    ]


def test_sing_box_serializes_negated_logical_group():
    tree = LogicalTree(
        root=_logical(
            LogicalOperator.NOT,
            _logical(
                LogicalOperator.AND,
                _rule(RuleType.DOMAIN_SUFFIX, "example.com"),
                _rule(RuleType.DOMAIN_KEYWORD, "ads"),
            ),
        )
    )

    assert serialize_sing_box(tree=tree) == {
        "type": "logical",
        "rules": [
            {"domain_suffix": "example.com"},
            {"domain_keyword": "ads"},
        ],
        "mode": "and",
        "invert": True,
    }


def test_sing_box_double_negation_restores_rule():
    tree = LogicalTree(
        root=_logical(
            LogicalOperator.NOT,
            _logical(
                LogicalOperator.NOT,
                _rule(RuleType.DOMAIN_SUFFIX, "example.com"),
            ),
        )
    )

    assert serialize_sing_box(tree=tree) == {
        "domain_suffix": "example.com",
        "invert": False,
    }
