import yaml
from yaml import CDumper

from .base import BaseSerialize


class Serialize(BaseSerialize):
    def serialize(self) -> str:
        yaml_data = {"no_resolve": self.option.no_resolve}
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
            return yaml.dump(yaml_data, sort_keys=False, Dumper=CDumper)
        return ""
