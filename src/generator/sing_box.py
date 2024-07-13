import json
import subprocess
from typing import Dict, List

from loguru import logger
from anytree import Node

from model import RuleModel, SourceModel
from config import DIR_PATH
from parser import Parser

field_format = {
    "domain": "domain",
    "domain-suffix": "domain_suffix",
    "domain-keyword": "domain_keyword",
    "ip-cidr": "ip_cidr",
    "ip-cidr6": "ip_cidr",
    "process-name": "process_name",
    "dest-port": "port",
    "src-port": "source_port",
    "src-ip": "source_ip_cidr",
}


class SingBoxError(Exception): ...


class UnsupportedRuleTypeError(SingBoxError):
    def __init__(self, rule_type: str):
        super().__init__(f"Unsupported rule type: {rule_type}")


class InvalidProtocolError(SingBoxError):
    def __init__(self, rule: str):
        super().__init__(f"Protocol only supports 'tcp' and 'udp'. Current: {rule}")


class GenerateLogicalError(SingBoxError): ...


def format_rule(rule_type: str, rule: str) -> Dict[str, str]:
    if formatted_rule_type := field_format.get(rule_type):
        return {formatted_rule_type: rule}
    if rule_type == "protocol":
        if rule in ["tcp", "udp"]:
            return {"network": rule}
        raise InvalidProtocolError(rule)

    raise UnsupportedRuleTypeError(rule_type)


class SingBoxGenerator:
    def __init__(self, *, info: SourceModel, rules: RuleModel) -> None:
        self.info = info
        self.rules = rules
        dir_path = DIR_PATH / "sing-box"
        dir_path.mkdir(exist_ok=True)
        self.json_path = dir_path / (info.filename + ".json")
        self.srs_path = self.json_path.with_suffix(".srs")

    def generate(self):
        json_data = {"version": 1, "rules": [{}]}
        if rules := self.rules.domain:
            json_data["rules"][0]["domain"] = rules
        if rules := self.rules.domain_suffix:
            json_data["rules"][0]["domain_suffix"] = rules
        if rules := self.rules.domain_keyword:
            json_data["rules"][0]["domain_keyword"] = rules
        if rules := self.rules.ip_cidr:
            json_data["rules"][0]["ip_cidr"] = rules
        if rules := self.rules.ip_cidr6:
            if json_data["rules"][0]["ip_cidr"]:
                json_data["rules"][0]["ip_cidr"].extend(rules)
            else:
                json_data["rules"][0]["ip_cidr"] = rules
        if rules := self.rules.process:
            if json_data["rules"][0]:
                json_data["rules"].append({"process_name": rules})
            else:
                json_data["rules"][0]["process_name"] = rules
        if rules := self.rules.logical:
            for rule in rules:
                try:
                    json_data["rules"].append(self.generate_logical(rule))
                except SingBoxError as e:
                    logger.error(f"rule: {rule}, err: {e}")

        if json_data["rules"][0]:
            with self.json_path.open("w") as f:
                json.dump(json_data, f)
            logger.success(f"{self.json_path} generated successfully")
            result = subprocess.run(
                ["sing-box", "rule-set", "compile", self.json_path],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                logger.success(f"{self.srs_path} generated successfully")
            else:
                logger.error(
                    f"{self.srs_path} generated failed, result: {result.stderr}"
                )

    @staticmethod
    def _generate_logical_node(node: Node) -> Dict[str, str | List[dict]]:
        if isinstance(node.name, tuple):
            return format_rule(node.name[0], node.name[1])
        if node.name == "not":
            return SingBoxGenerator._generate_logical_not(node)
        return SingBoxGenerator._generate_logical_node_base(node)

    @staticmethod
    def _generate_logical_node_base(node: Node) -> Dict[str, str | List[dict]]:
        rule = {"type": "logical", "rules": [], "mode": node.name}
        for child in node.children:
            rule["rules"].append(SingBoxGenerator._generate_logical_node(child))
        return rule

    @staticmethod
    def _generate_logical_not(node: Node) -> Dict[str, str | List[dict]]:
        sub_node = node.children[0]
        if isinstance(sub_node.name, tuple):
            rule = format_rule(sub_node.name[0], sub_node.name[1])
            rule["invert"] = True
            return rule
        if sub_node.name == "not":
            raise GenerateLogicalError(
                "The sub-rule of a 'not' logic cannot be another 'not' logic"
            )
        rule = {"type": "logical", "rules": [], "mode": sub_node.name, "invert": True}
        for child in sub_node.children:
            rule["rules"].append(SingBoxGenerator._generate_logical_node(child))
        return rule

    @staticmethod
    def generate_logical(rule: str) -> Dict[str, List[Dict[str, str]] | str]:
        logical_rule = {"type": "logical", "rules": []}
        root_node = Parser.parse_logical_rule(rule)

        if root_node.name == "not":
            logical_rule = SingBoxGenerator._generate_logical_not(root_node)
        else:
            logical_rule["mode"] = root_node.name
            for child in root_node.children:
                logical_rule["rules"].append(
                    SingBoxGenerator._generate_logical_node(child)
                )
        return logical_rule


if __name__ == "__main__":
    logger.debug(
        SingBoxGenerator.generate_logical(
            "AND,((PROTOCOL,UDP), (DOMAIN-SUFFIX,googlevideo.com))"
        )
    )
    logger.debug(
        SingBoxGenerator.generate_logical(
            "AND,((PROTOCOL,UDP), (OR,((DOMAIN-KEYWORD,bilibili), (DOMAIN-KEYWORD,biliapi), (DOMAIN-KEYWORD,mcdn), (DOMAIN-KEYWORD,douyu))))"
        )
    )
    logger.debug(
        SingBoxGenerator.generate_logical("NOT,((OR,((DOMAIN,a.com),(DOMAIN,b.com))))")
    )
    try:
        logger.debug(SingBoxGenerator.generate_logical("NOT,((PROTOCOL,QUIC))"))
    except Exception as e:
        logger.error(e)

    logger.debug(
        SingBoxGenerator.generate_logical(
            "NOT,((AND,((DOMAIN-SUFFIX,baidu.com), (NOT,((PROTOCOL,UDP))))))"
        )
    )

    try:
        logger.debug(
            SingBoxGenerator.generate_logical(
                "NOT,((NOT,((DOMAIN-SUFFiX, baidu.com))))"
            )
        )
    except Exception as e:
        logger.error(e)
