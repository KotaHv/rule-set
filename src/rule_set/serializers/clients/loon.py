from typing import override

from rule_set.models import SerializableRuleModel
from rule_set.utils.domain import regex_to_wildcard

from ..logic import surge_logical_serialize
from .base import BaseRuleSerializer

include_rule_types = [
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-WILDCARD",
    "DOMAIN-KEYWORD",
    "IP-CIDR",
    "IP-CIDR6",
    "GEOIP",
    "IP-ASN",
    "USER-AGENT",
    "URL-REGEX",
    "SRC-PORT",
    "DEST-PORT",
    "PROTOCOL",
    "PROCESS-NAME",
]


class LoonSerializer(BaseRuleSerializer[str]):
    @override
    def serialize(self, rules: SerializableRuleModel) -> str:
        serialized_rules: list[str] = []

        serialized_rules.extend(f"DOMAIN,{domain}" for domain in rules.domain)

        serialized_rules.extend(
            f"DOMAIN-SUFFIX,{domain_suffix}" for domain_suffix in rules.domain_suffix
        )

        serialized_rules.extend(
            f"DOMAIN-WILDCARD,{domain_wildcard}"
            for domain_wildcard in rules.domain_wildcard
        )

        serialized_rules.extend(
            f"DOMAIN-KEYWORD,{domain_keyword}"
            for domain_keyword in rules.domain_keyword
        )

        serialized_rules.extend(f"IP-CIDR,{ip_cidr}" for ip_cidr in rules.ip_cidr)

        serialized_rules.extend(f"IP-CIDR6,{ip_cidr6}" for ip_cidr6 in rules.ip_cidr6)

        serialized_rules.extend(f"IP-ASN,{ip_asn}" for ip_asn in rules.ip_asn)

        serialized_rules.extend(f"USER-AGENT,{ua}" for ua in rules.user_agent)

        serialized_rules.extend(f"PROCESS-NAME,{process}" for process in rules.process)

        serialized_rules.extend(
            rule
            for tree in rules.logical
            if (rule := surge_logical_serialize(tree=tree, include=include_rule_types))
            is not None
        )

        serialized_rules.extend(
            f"URL-REGEX,{url_regex}" for url_regex in rules.url_regex
        )
        serialized_rules.extend(
            f"DOMAIN-WILDCARD,{wildcard}"
            for domain_regex in rules.domain_regex
            for wildcard in regex_to_wildcard(domain_regex)
        )
        filtered_rules = list(filter(None, serialized_rules))
        content = "\n".join(filtered_rules)
        if content:
            content = f"# Total: {len(filtered_rules)} rules\n# Last Updated: {self.last_updated}\n{content}"
        return content
