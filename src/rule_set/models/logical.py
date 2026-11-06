from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, field_validator, model_validator


class LogicalOperator(StrEnum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class RuleType(StrEnum):
    DOMAIN = "DOMAIN"
    DOMAIN_SUFFIX = "DOMAIN-SUFFIX"
    DOMAIN_KEYWORD = "DOMAIN-KEYWORD"
    DOMAIN_WILDCARD = "DOMAIN-WILDCARD"
    IP_CIDR = "IP-CIDR"
    IP_CIDR6 = "IP-CIDR6"
    IP_ASN = "IP-ASN"
    GEOIP = "GEOIP"
    USER_AGENT = "USER-AGENT"
    PROCESS_NAME = "PROCESS-NAME"
    SRC_IP = "SRC-IP"
    IN_PORT = "IN-PORT"
    DEST_PORT = "DEST-PORT"
    PROTOCOL = "PROTOCOL"
    HOSTNAME_TYPE = "HOSTNAME-TYPE"


class ConcreteRule(BaseModel, frozen=True):
    rule_type: RuleType
    rule_values: tuple[str, ...]

    @field_validator("rule_values")
    @classmethod
    def validate_rule_values(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        values = tuple(stripped for value in v if (stripped := value.strip()))
        if not values:
            raise ValueError("Rule values cannot be empty")
        return values


class Rule(BaseModel, frozen=True):
    rule: ConcreteRule


class Logical(BaseModel, frozen=True):
    op: Literal[LogicalOperator.AND, LogicalOperator.OR, LogicalOperator.NOT]
    children: tuple[Node, ...]

    @model_validator(mode="after")
    def validate_arity(self) -> Self:
        if self.op is LogicalOperator.NOT:
            if len(self.children) != 1:
                raise ValueError("NOT node must have exactly one child")
        elif len(self.children) < 2:
            raise ValueError("AND/OR node must have at least two children")
        return self


type Node = Rule | Logical
type SortKey = tuple[int, str, tuple[str, ...], tuple[SortKey, ...]]

_LOGICAL_PRIORITY = {
    LogicalOperator.AND: 1,
    LogicalOperator.NOT: 2,
    LogicalOperator.OR: 3,
}


def _rule_key(rule: ConcreteRule) -> SortKey:
    return (0, rule.rule_type.value, rule.rule_values, ())


def _logical_key(node: Logical, children: tuple[SortKey, ...]) -> SortKey:
    return (_LOGICAL_PRIORITY[node.op], "", (), children)


def _child_keys(node: Logical) -> list[SortKey]:
    keys: list[SortKey] = []
    for child in node.children:
        if (
            node.op in (LogicalOperator.AND, LogicalOperator.OR)
            and isinstance(child, Logical)
            and child.op is node.op
        ):
            keys.extend(_child_keys(child))
        else:
            keys.append(canonical_key(child))
    return keys


def canonical_key(node: Node) -> SortKey:
    if isinstance(node, Rule):
        return _rule_key(node.rule)
    return _logical_key(node, tuple(sorted(_child_keys(node))))


def output_sort_key(node: Node) -> SortKey:
    if isinstance(node, Rule):
        return _rule_key(node.rule)
    return _logical_key(
        node,
        tuple(output_sort_key(child) for child in node.children),
    )


class LogicalTree(BaseModel, frozen=True):
    root: Logical

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LogicalTree):
            return NotImplemented
        return canonical_key(self.root) == canonical_key(other.root)

    def __hash__(self) -> int:
        return hash(canonical_key(self.root))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, LogicalTree):
            return NotImplemented
        return canonical_key(self.root) < canonical_key(other.root)
