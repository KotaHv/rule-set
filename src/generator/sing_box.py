import json
import subprocess

from loguru import logger

from model import RuleModel, SourceModel
from config import DIR_PATH


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
