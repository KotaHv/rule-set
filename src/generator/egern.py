import yaml

from pathlib import Path

from loguru import logger

from model import RuleModel, SourceModel


class EgernGenerator:
    def __init__(self, *, info: SourceModel, rules: RuleModel) -> None:
        self.info = info
        self.rules = rules
        dir_path = Path("Egern")
        dir_path.mkdir(exist_ok=True)
        self.path = dir_path / (info.filename + ".yaml")

    def generate(self):
        yaml_data = {"no_resolve": self.info.no_resolve}
        if self.rules.domain:
            yaml_data["domain_set"] = list(self.rules.domain)
        if self.rules.domain_keyword:
            yaml_data["domain_keyword_set"] = list(self.rules.domain_keyword)
        if self.rules.domain_suffix:
            yaml_data["domain_suffix_set"] = list(self.rules.domain_suffix)
        if self.rules.ip_cidr:
            yaml_data["ip_cidr_set"] = list(self.rules.ip_cidr)
        if self.rules.ip_cidr6:
            yaml_data["ip_cidr6_set"] = list(self.rules.ip_cidr6)
        if self.rules.ip_asn:
            yaml_data["asn_set"] = list(self.rules.ip_asn)
        if len(yaml_data.keys()) > 1:
            with self.path.open("w") as f:
                yaml.dump(yaml_data, f, sort_keys=False)
            logger.success(f"{self.path} generated successfully")
