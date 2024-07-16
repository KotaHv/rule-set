import json
import subprocess

from loguru import logger

import logic_rule_proc
from model import RuleModel, SourceModel
from config import DIR_PATH

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


class SingBoxGenerator:
    def __init__(self, *, info: SourceModel, rules: RuleModel) -> None:
        self.info = info
        self.rules = rules
        dir_path = DIR_PATH / "sing-box"
        self.json_path = dir_path / (info.target_name + ".json")
        self.srs_path = self.json_path.with_suffix(".srs")
        self.json_with_logical_path = dir_path / (
            info.target_name + "-logical" + ".json"
        )
        self.srs_with_logical_path = self.json_with_logical_path.with_suffix(".srs")
        self.json_path.parent.mkdir(parents=True, exist_ok=True)

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
        else:
            return
        if rules := self.rules.logical:
            logical_rule_generated = False
            for rule in rules:
                logical_rule = logic_rule_proc.SingBoxSerialize(rule).serialize()
                if logical_rule:
                    json_data["rules"].append(logical_rule)
                    logical_rule_generated = True
            if not logical_rule_generated:
                return
            if json_data["rules"][0]:
                with self.json_with_logical_path.open("w") as f:
                    json.dump(json_data, f)
                logger.success(f"{self.json_with_logical_path} generated successfully")
                result = subprocess.run(
                    ["sing-box", "rule-set", "compile", self.json_with_logical_path],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    logger.success(
                        f"{self.srs_with_logical_path} generated successfully"
                    )
                else:
                    logger.error(
                        f"{self.srs_with_logical_path} generated failed, result: {result.stderr}"
                    )
