from .base import BaseSerialize
from ..logical import surge_logical_serialize


include_rule_types = [
    "DOMAIN",
    "DOMAIN-SUFFIX",
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
]


class Serialize(BaseSerialize):
    def serialize(self) -> str:
        rules = []
        if self.rules.domain:
            rules.extend([f"DOMAIN,{domain}" for domain in self.rules.domain])
        if self.rules.domain_suffix:
            rules.extend(
                [
                    f"DOMAIN-SUFFIX,{domain_suffix}"
                    for domain_suffix in self.rules.domain_suffix
                ]
            )
        if self.rules.domain_keyword:
            rules.extend(
                [
                    f"DOMAIN-KEYWORD,{domain_keyword}"
                    for domain_keyword in self.rules.domain_keyword
                ]
            )
        if self.rules.ip_cidr:
            rules.extend([f"IP-CIDR,{ip_cidr}" for ip_cidr in self.rules.ip_cidr])
        if self.rules.ip_cidr6:
            rules.extend([f"IP-CIDR6,{ip_cidr6}" for ip_cidr6 in self.rules.ip_cidr6])
        if self.rules.ip_asn:
            rules.extend([f"IP-ASN,{ip_asn}" for ip_asn in self.rules.ip_asn])
        if self.rules.ua:
            rules.extend([f"USER-AGENT,{ua}" for ua in self.rules.ua])
        if self.rules.logical:
            rules.extend(
                [
                    surge_logical_serialize(root_node=node, include=include_rule_types)
                    for node in self.rules.logical
                ]
            )
        return "\n".join(filter(None, rules))
