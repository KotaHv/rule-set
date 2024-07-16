import yaml

from yaml import CDumper
from loguru import logger

from model import RuleModel, SourceModel
from config import DIR_PATH


class EgernGenerator:
    def __init__(self, *, info: SourceModel, rules: RuleModel) -> None:
        self.info = info
        self.rules = rules
        dir_path = DIR_PATH / "Egern"
        self.path = dir_path / info.target_name.with_suffix(".yaml")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def generate(self):
        yaml_data = {"no_resolve": self.info.no_resolve}
        if self.rules.domain:
            yaml_data["domain_set"] = self.rules.domain
        if self.rules.domain_suffix:
            yaml_data["domain_suffix_set"] = self.rules.domain_suffix
        if self.rules.domain_keyword:
            yaml_data["domain_keyword_set"] = self.rules.domain_keyword
        if self.rules.ip_cidr:
            yaml_data["ip_cidr_set"] = self.rules.ip_cidr
        if self.rules.ip_cidr6:
            yaml_data["ip_cidr6_set"] = self.rules.ip_cidr6
        if self.rules.ip_asn:
            yaml_data["asn_set"] = self.rules.ip_asn
        if len(yaml_data.keys()) > 1:
            with self.path.open("w") as f:
                yaml.dump(yaml_data, f, sort_keys=False, Dumper=CDumper)
            logger.success(f"{self.path} generated successfully")
