import yaml
from yaml import CDumper

from utils import domain

from .base import BaseSerialize
from ..logical.egern import serialize as logical_serialize


class Serialize(BaseSerialize):
    def serialize(self) -> str:
        yaml_data = {"no_resolve": self.option.serialization.no_resolve}
        logical_rules = list(
            filter(
                None, [logical_serialize(root_node=rule) for rule in self.rules.logical]
            )
        )
        if self.rules.domain:
            yaml_data["domain_set"] = self.rules.domain
        if self.rules.domain_suffix:
            yaml_data["domain_suffix_set"] = self.rules.domain_suffix
        if self.rules.domain_wildcard:
            yaml_data["domain_regex_set"] = [
                domain.wildcard_to_regex(domain_wildcard)
                for domain_wildcard in self.rules.domain_wildcard
            ]
        if logical_rules:
            if yaml_data.get("domain_regex_set"):
                yaml_data["domain_regex_set"].extend(logical_rules)
            else:
                yaml_data["domain_regex_set"] = logical_rules
        if self.rules.domain_keyword:
            yaml_data["domain_keyword_set"] = self.rules.domain_keyword
        if self.rules.ip_cidr:
            yaml_data["ip_cidr_set"] = self.rules.ip_cidr
        if self.rules.ip_cidr6:
            yaml_data["ip_cidr6_set"] = self.rules.ip_cidr6
        if self.rules.ip_asn:
            yaml_data["asn_set"] = self.rules.ip_asn
        if len(yaml_data.keys()) > 1:
            # Calculate total rules count
            rule_count = 0
            for key, value in yaml_data.items():
                if key != "no_resolve" and isinstance(value, list):
                    rule_count += len(value)

            yaml_content = yaml.dump(yaml_data, sort_keys=False, Dumper=CDumper)
            if rule_count > 0:
                return f"# Total: {rule_count} rules\n{yaml_content}"
            return yaml_content
        return ""
