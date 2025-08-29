from anytree import Node
from loguru import logger

from serialize.error import UnsupportedRuleTypeError, SerializeError
from utils import is_logical_keyword, is_logical_not, is_logical_and_or
from serialize.logical import surge_logical_serialize

type_format = {
    "domain-suffix": "domain_suffix",
    "domain-keyword": "domain_keyword",
    "domain-regex": "domain_regex",
    "ip-cidr": "ip_cidr",
    "ip-cidr6": "ip_cidr",
    "process-name": "process_name",
    "process-path": "process_path",
    "dest-port": "port",
    "src-port": "source_port",
    "src-ip": "source_ip_cidr",
    "src-ip-cidr": "source_ip_cidr",
}

include_types = [
    "query_type",
    "network",
    "domain",
    "domain_suffix",
    "domain_keyword",
    "domain_regex",
    "source_ip_cidr",
    "ip_cidr",
    "source_port",
    "source_port_range",
    "port",
    "port_range",
    "process_name",
    "process_path",
    "package_name",
    "wifi_ssid",
    "wifi_bssid",
]


def serialize(*, root_node: Node) -> dict | None:
    for node in [root_node, *root_node.descendants]:
        if isinstance(node.name, str):
            node.name = node.name.lower()
    try:
        return _serialize(root_node)
    except SerializeError as e:
        logger.error(e)
    except Exception as e:
        logger.error(
            f"rule: '{surge_logical_serialize(root_node=root_node)}', err: {e}"
        )


def _serialize(node: Node) -> dict[str, list[dict[str, str]] | str]:
    if isinstance(node.name, tuple):
        return format_rule(node.name[0], node.name[1])
    mode = node.name
    if not is_logical_keyword(mode):
        raise SerializeError(
            f"{mode} is not a valid logical operator. Valid operators are: AND, OR, NOT",
            node=node.root,
        )
    if is_logical_not(mode) and len(node.children) != 1:
        raise SerializeError(
            "NOT rule must only have one sub-rule",
            node=node.root,
        )
    elif is_logical_and_or(mode) and len(node.children) < 2:
        raise SerializeError(
            "AND/OR rule must have at least two sub-rules",
            node=node.root,
        )
    if mode == "not":
        rule = _serialize_not(node)
    else:
        rule = {"type": "logical", "rules": [], "mode": mode}
        for child_node in node.children:
            rule["rules"].append(_serialize(child_node))
    return rule


def _serialize_not(
    node: Node, invert: bool = True
) -> dict[str, list[dict[str, str]] | str]:
    child_node = node.children[0]
    if isinstance(child_node.name, tuple):
        if len(node.children) != 1:
            raise SerializeError("NOT rule must only have one sub-rule")
        rule = format_rule(child_node.name[0], child_node.name[1])
        rule["invert"] = invert
        return rule
    if child_node.name == "not":
        return _serialize_not(child_node, invert=not invert)
    rule = {
        "type": "logical",
        "rules": [],
        "mode": child_node.name,
        "invert": invert,
    }
    for child_node in child_node.children:
        rule["rules"].append(_serialize(child_node))
    return rule


def format_rule(rule_type: str, rule: str) -> dict[str, str]:
    rule_type = rule_type.lower()
    rule_type = type_format.get(rule_type, rule_type)
    if rule_type in include_types:
        if rule_type == "port":
            return {"port": int(rule)}
        return {rule_type: rule}
    if rule_type == "protocol" and rule.upper() in ["UDP", "TCP"]:
        return {"network": rule.lower()}
    raise UnsupportedRuleTypeError(rule_type)
