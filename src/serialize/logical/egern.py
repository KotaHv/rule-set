from anytree import Node
from loguru import logger

from utils import domain, is_logical_keyword, is_logical_not, is_logical_and_or

from ..error import SerializeError, UnsupportedRuleTypeError
from .surge import serialize as surge_logical_serialize

include_type = [
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-WILDCARD",
    "DOMAIN-KEYWORD",
    "DOMAIN-REGEX",
]


def serialize(*, root_node: Node) -> str | None:
    for node in [root_node, *root_node.descendants]:
        if isinstance(node.name, str):
            node.name = node.name.lower()
    try:
        rule = _serialize(root_node.name, root_node)
        if isinstance(rule, list):
            rule = "|".join(rule)
        return rule
    except SerializeError as e:
        logger.error(e)
    except Exception as e:
        logger.error(
            f"rule: '{surge_logical_serialize(root_node=root_node)}', err: {e}"
        )


def _serialize(logical_type: str, node: Node) -> list[str] | str:
    if isinstance(node.name, tuple):
        rule = format_rule(logical_type, node.name[0], node.name[1])
        return rule
    if not is_logical_keyword(node.name):
        raise SerializeError(
            f"{node.name} is not a valid logical operator. Valid operators are: AND, OR, NOT",
            node=node.root,
        )
    if is_logical_not(node.name) and len(node.children) != 1:
        raise SerializeError(
            "NOT rule must only have one sub-rule",
            node=node.root,
        )
    elif is_logical_and_or(node.name) and len(node.children) < 2:
        raise SerializeError(
            "AND/OR rule must have at least two sub-rules",
            node=node.root,
        )
    rule = []
    for child_node in node.children:
        rule.append(_serialize(node.name, child_node))
    if node.name == "not":
        rule = rule[0]
        if isinstance(rule, list):
            for i, r in enumerate(rule):
                rule[i] = f"(?!{r})"
            rule = f"(^{''.join(rule)})"
        else:
            rule = f"(?!{rule})"
    elif node.name == "and":
        for i, r in enumerate(rule):
            if isinstance(r, list):
                rule[i] = rf"(?=[\w.-]*?({'|'.join(r)}))"
            else:
                if not r.startswith("(?") or r.startswith("(^"):
                    rule[i] = rf"(?=[\w.-]*?{r})"
        rule = "".join(rule)
    return rule


def _format_rule(rule_type: str, rule: str) -> str:
    if rule_type not in include_type:
        raise UnsupportedRuleTypeError(rule_type)
    if rule_type == "DOMAIN":
        return domain.domain_to_regex(rule)
    if rule_type == "DOMAIN-SUFFIX":
        return domain.suffix_to_regex(rule)
    if rule_type == "DOMAIN-WILDCARD":
        return domain.wildcard_to_regex(rule)
    if rule_type == "DOMAIN-KEYWORD":
        return domain.keyword_to_regex(rule)
    if rule_type == "DOMAIN-REGEX":
        return rule


def format_rule(logical_type: str, rule_type: str, rule: str) -> str:
    rule = _format_rule(rule_type, rule)
    if logical_type == "not":
        if rule_type in ["DOMAIN", "DOMAIN-WILDCARD"]:
            rule = rule.replace("^", "^(?!") + ")"
        elif rule_type in ["DOMAIN-KEYWORD", "DOMAIN-REGEX"]:
            rule = rf"(?![\w.-]*?{rule})"
        else:
            rule = rf"(?!{rule})"
    elif logical_type == "and":
        if rule_type in ["DOMAIN", "DOMAIN-WILDCARD"]:
            rule = rule.replace("^", "^(?=") + ")"
        elif rule_type in ["DOMAIN-KEYWORD", "DOMAIN-REGEX"]:
            rule = rf"(?=[\w.-]*?{rule})"
        else:
            rule = rf"(?={rule})"
    return rule


if __name__ == "__main__":
    from deserialize.logical import deserialize as logical_deserialize

    root_node = logical_deserialize(
        "OR,((DOMAIN-KEYWORD,xxx), (AND,((DOMAIN-KEYWORD,yyy), (DOMAIN-SUFFIX,cn))))"
    )
    print(serialize(root_node=root_node))
