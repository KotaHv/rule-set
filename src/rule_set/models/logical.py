from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator


class LogicalOperator(StrEnum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class LogicalNodeType(StrEnum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    RULE = "RULE"


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


class ConcreteRule(BaseModel):
    """Represents a concrete rule with type and values."""

    rule_type: RuleType
    rule_values: tuple[str, ...]

    @field_validator("rule_values")
    @classmethod
    def validate_rule_values(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        """Validate rule values are not empty."""
        if not v:
            raise ValueError("Rule values cannot be empty")
        return tuple(val.strip() for val in v if val.strip())

    def render(self) -> str:
        return f"({self.rule_type.value},{','.join(self.rule_values)})"

    def __eq__(self, other: object) -> bool:
        """Compare two concrete rules for equality."""
        if not isinstance(other, ConcreteRule):
            return False
        return (
            self.rule_type == other.rule_type and self.rule_values == other.rule_values
        )

    def __hash__(self) -> int:
        """Hash based on rule type and values."""
        return hash((self.rule_type, self.rule_values))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, ConcreteRule):
            return NotImplemented
        if self.rule_type == other.rule_type:
            return self.rule_values < other.rule_values
        return self.rule_type < other.rule_type


class LogicalNode(BaseModel, ABC):
    """Abstract base class for all logical nodes."""

    parent: LogicalNode | None = Field(default=None, exclude=True, repr=False)

    @abstractmethod
    def get_children(self) -> tuple[LogicalNode, ...]:
        """Get child nodes."""
        pass

    @abstractmethod
    def render(self, prefix: str = "", is_last: bool = True) -> str:
        """Render node as string for debugging."""
        pass


class AndNode(LogicalNode):
    """Represents an AND logical operation."""

    children: tuple[LogicalNodeAnnotated, ...] = Field(
        default_factory=tuple, min_length=2
    )
    node_type: Literal[LogicalNodeType.AND] = LogicalNodeType.AND

    @property
    def operator(self) -> Literal[LogicalOperator.AND]:
        return LogicalOperator.AND

    @model_validator(mode="after")
    def validate_children(self) -> Self:
        """Ensure AND node has at least 2 children."""
        if len(self.children) < 2:
            raise ValueError("AND node must have at least 2 children")
        # Set parent references
        for child in self.children:
            child.parent = self
        return self

    def get_children(self) -> tuple[LogicalNode, ...]:
        return self.children

    def render(self, prefix: str = "", is_last: bool = True) -> str:
        """Render AND node."""
        if self.parent is None:
            result = "AND\n"
            new_prefix = ""
        else:
            result = f"{prefix}{'└── ' if is_last else '├── '}AND\n"
            new_prefix = prefix + ("    " if is_last else "│   ")

        for i, child in enumerate(self.children):
            result += child.render(new_prefix, i == len(self.children) - 1)

        return result

    def __eq__(self, other: object) -> bool:
        """Compare two AND nodes for equality."""
        if not isinstance(other, AndNode):
            return False
        if len(self.children) != len(other.children):
            return False
        return all(
            self_child == other_child
            for self_child, other_child in zip(
                self.children, other.children, strict=False
            )
        )

    def __hash__(self) -> int:
        """Hash based on node type and children."""
        return hash((self.node_type, self.children))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, LogicalNode):
            return NotImplemented
        if type(self) is not type(other):
            return NODE_PRIORITY[type(self)] < NODE_PRIORITY[type(other)]
        return self.children < other.children


class OrNode(LogicalNode):
    """Represents an OR logical operation."""

    children: tuple[LogicalNodeAnnotated, ...] = Field(
        default_factory=tuple, min_length=2
    )
    node_type: Literal[LogicalNodeType.OR] = LogicalNodeType.OR

    @property
    def operator(self) -> Literal[LogicalOperator.OR]:
        return LogicalOperator.OR

    @model_validator(mode="after")
    def validate_children(self) -> Self:
        """Ensure OR node has at least 2 children."""
        if len(self.children) < 2:
            raise ValueError("OR node must have at least 2 children")
        # Set parent references
        for child in self.children:
            child.parent = self
        return self

    def get_children(self) -> tuple[LogicalNode, ...]:
        return self.children

    def render(self, prefix: str = "", is_last: bool = True) -> str:
        """Render OR node."""
        if self.parent is None:
            result = "OR\n"
            new_prefix = ""
        else:
            result = f"{prefix}{'└── ' if is_last else '├── '}OR\n"
            new_prefix = prefix + ("    " if is_last else "│   ")

        for i, child in enumerate(self.children):
            result += child.render(new_prefix, i == len(self.children) - 1)

        return result

    def __eq__(self, other: object) -> bool:
        """Compare two OR nodes for equality."""
        if not isinstance(other, OrNode):
            return False
        if len(self.children) != len(other.children):
            return False
        return all(
            self_child == other_child
            for self_child, other_child in zip(
                self.children, other.children, strict=False
            )
        )

    def __hash__(self) -> int:
        """Hash based on node type and children."""
        return hash((self.node_type, self.children))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, LogicalNode):
            return NotImplemented
        if type(self) is not type(other):
            return NODE_PRIORITY[type(self)] < NODE_PRIORITY[type(other)]
        return self.children < other.children


class NotNode(LogicalNode):
    """Represents a NOT logical operation."""

    child: LogicalNodeAnnotated = Field(
        description="The single child node for NOT operation"
    )
    node_type: Literal[LogicalNodeType.NOT] = LogicalNodeType.NOT

    @property
    def operator(self) -> Literal[LogicalOperator.NOT]:
        return LogicalOperator.NOT

    @model_validator(mode="after")
    def validate_child(self) -> Self:
        """Ensure NOT node has exactly one child."""
        if not hasattr(self, "child"):
            raise ValueError("NOT node must have exactly one child")
        # Set parent reference
        self.child.parent = self
        return self

    def get_children(self) -> tuple[LogicalNode, ...]:
        return (self.child,)

    def render(self, prefix: str = "", is_last: bool = True) -> str:
        """Render NOT node."""
        if self.parent is None:
            result = "NOT\n"
            new_prefix = ""
        else:
            result = f"{prefix}{'└── ' if is_last else '├── '}NOT\n"
            new_prefix = prefix + ("    " if is_last else "│   ")

        result += self.child.render(new_prefix, True)
        return result

    def __eq__(self, other: object) -> bool:
        """Compare two NOT nodes for equality."""
        if not isinstance(other, NotNode):
            return False
        return self.child == other.child

    def __hash__(self) -> int:
        """Hash based on node type and child."""
        return hash((self.node_type, self.child))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, LogicalNode):
            return NotImplemented
        if type(self) is not type(other):
            return NODE_PRIORITY[type(self)] < NODE_PRIORITY[type(other)]
        return self.child < other.child


class RuleNode(LogicalNode):
    """Represents a concrete rule."""

    rule: ConcreteRule
    node_type: Literal[LogicalNodeType.RULE] = LogicalNodeType.RULE

    def get_children(self) -> tuple[LogicalNode, ...]:
        return ()

    def render(self, prefix: str = "", is_last: bool = True) -> str:
        """Render rule node."""
        return f"{prefix}{'└── ' if is_last else '├── '}{self.rule.render()}\n"

    def __eq__(self, other: object) -> bool:
        """Compare two rule nodes for equality."""
        if not isinstance(other, RuleNode):
            return False
        return self.rule == other.rule

    def __hash__(self) -> int:
        """Hash based on node type and rule."""
        return hash((self.node_type, self.rule))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, LogicalNode):
            return NotImplemented
        if type(self) is not type(other):
            return NODE_PRIORITY[type(self)] < NODE_PRIORITY[type(other)]
        return self.rule < other.rule


NODE_PRIORITY = {
    RuleNode: 0,
    AndNode: 1,
    NotNode: 2,
    OrNode: 3,
}
LogicalNodeUnion = AndNode | OrNode | NotNode | RuleNode
LogicalNodeAnnotated = Annotated[LogicalNodeUnion, Field(discriminator="node_type")]


class LogicalTree(BaseModel):
    """Container for logical rule trees."""

    root: AndNode | OrNode | NotNode = Field(
        discriminator="node_type"
    )  # Only logical operation nodes as root

    def render(self) -> str:
        """Render tree as string for debugging."""
        return self.root.render()

    def __eq__(self, other: object) -> bool:
        """Compare two logical trees for equality."""
        if not isinstance(other, LogicalTree):
            return False
        return self.root == other.root

    def __hash__(self) -> int:
        """Hash based on root node."""
        return hash(self.root)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, LogicalTree):
            return NotImplemented
        return self.root < other.root
