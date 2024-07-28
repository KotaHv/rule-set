from loguru import logger

from model import RuleModel
from .base import BaseDeserialize
from deserialize import logical
from utils import is_logical_keyword, validate_domain


class RuleSetDeserialize(BaseDeserialize):
    def deserialize(self) -> RuleModel:
        unique_node_list = []
        for line in self.data_lines:
            processed_line = line.split(",")
            rule_type, rule = processed_line[0].lower(), processed_line[1].strip()
            if rule_type == "domain":
                if not validate_domain(rule):
                    logger.warning(f"Invalid domain: '{rule}'")
                    continue
                self.result.domain.add(rule)
            elif rule_type == "domain-suffix":
                if not validate_domain(rule):
                    logger.warning(f"Invalid domain: '{rule}'")
                    continue
                self.result.domain_suffix.add(rule)
            elif rule_type == "domain-keyword":
                self.result.domain_keyword.add(rule)
            elif rule_type == "domain-wildcard":
                self.result.domain_wildcard.add(rule)
            elif rule_type == "ip-cidr":
                self.result.ip_cidr.add(rule)
            elif rule_type == "ip-cidr6":
                self.result.ip_cidr6.add(rule)
            elif rule_type == "ip-asn":
                self.result.ip_asn.add(rule)
            # elif rule_type == "user-agent":
            #     self.result.ua.add(rule)
            # elif rule_type == "process-name":
            #     self.result.process.add(rule)
            elif is_logical_keyword(rule_type):
                node = logical.deserialize(line)
                if node is None:
                    continue
                if line not in unique_node_list:
                    unique_node_list.append(line)
                    self.result.logical.append(node)
            else:
                logger.warning(line)
        return self.result
