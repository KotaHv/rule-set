from typing import Dict, List

from anytree import Node
from loguru import logger

from .error import UnsupportedRuleTypeError, SerializeError


def _serialize(*, node: Node, include: List[str] | None = None) -> str:
    if isinstance(node.name, tuple):
        if include is not None and node.name[0].upper() not in include:
            raise UnsupportedRuleTypeError(node.name[0])
        return f"({",".join(node.name)}),"
    if node.name.upper() not in ["AND", "OR", "NOT"]:
        raise SerializeError(
            f"{node.name} is not a valid logical operator. Valid operators are: AND, OR, NOT",
            node=node.root,
        )
    if node.name == "NOT" and len(node.children) != 1:
        raise SerializeError(
            "NOT rule must only have one sub-rule",
            node=node.root,
        )
    elif node.name in ("AND", "OR") and len(node.children) < 2:
        raise SerializeError(
            "AND/OR rule must have at least two sub-rules",
            node=node.root,
        )
    rule = f"({node.name},("
    for child in node.children:
        rule += _serialize(node=child, include=include)
    rule = rule.rstrip(",") + ")),"
    return rule


def serialize(*, node: Node, include: List[str] | None = None) -> str | None:
    try:
        return _serialize(node=node, include=include)[1:-2]
    except UnsupportedRuleTypeError as e:
        logger.error(f"rule: {_serialize(node=node)}, err: {e}")
    except SerializeError as e:
        logger.error(e)


class SingBoxSerialize:
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

    def __init__(self, root_node: Node) -> None:
        for node in [root_node, *root_node.descendants]:
            if isinstance(node.name, str):
                node.name = node.name.lower()
        self.root_node = root_node

    def serialize(self) -> Dict[str, List[Dict[str, str]] | str] | None:
        try:
            return self._serialize(self.root_node)
        except SerializeError as e:
            logger.error(e)
        except Exception as e:
            logger.error(f"rule: '{_serialize(node=self.root_node)}', err: {e}")

    def _serialize(self, node: Node) -> Dict[str, List[Dict[str, str]] | str]:
        if isinstance(node.name, tuple):
            return self.format_rule(node.name[0], node.name[1])
        mode = node.name
        if mode not in ["and", "or", "not"]:
            raise SerializeError(
                f"{mode} is not a valid logical operator. Valid operators are: AND, OR, NOT",
                node=node.root,
            )
        if mode == "not" and len(node.children) != 1:
            raise SerializeError(
                "NOT rule must only have one sub-rule",
                node=node.root,
            )
        elif mode in ("and", "or") and len(node.children) < 2:
            raise SerializeError(
                "AND/OR rule must have at least two sub-rules",
                node=node.root,
            )
        if mode == "not":
            rule = self._serialize_not(node)
        else:
            rule = {"type": "logical", "rules": [], "mode": mode}
            for child_node in node.children:
                rule["rules"].append(self._serialize(child_node))
        return rule

    def _serialize_not(
        self, node: Node, invert: bool = True
    ) -> Dict[str, List[Dict[str, str]] | str]:
        child_node = node.children[0]
        if isinstance(child_node.name, tuple):
            if len(node.children) != 1:
                raise SerializeError("NOT rule must only have one sub-rule")
            rule = self.format_rule(child_node.name[0], child_node.name[1])
            rule["invert"] = invert
            return rule
        if child_node.name == "not":
            return self._serialize_not(child_node, invert=not invert)
        rule = {
            "type": "logical",
            "rules": [],
            "mode": child_node.name,
            "invert": invert,
        }
        for child_node in child_node.children:
            rule["rules"].append(self._serialize(child_node))
        return rule

    def format_rule(self, rule_type: str, rule: str) -> Dict[str, str]:
        rule_type = rule_type.lower()
        rule_type = self.type_format.get(rule_type, rule_type)
        if rule_type in self.include_types:
            return {rule_type: rule}
        raise UnsupportedRuleTypeError(rule_type)
