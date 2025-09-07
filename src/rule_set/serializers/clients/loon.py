from ..logic import surge_logical_serialize
from .base import BaseSerializer

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


class LoonSerializer(BaseSerializer):
    def serialize(self) -> str:
        rules = []

        rules.extend(f"DOMAIN,{domain}" for domain in self.rules.domain)

        rules.extend(
            f"DOMAIN-SUFFIX,{domain_suffix}"
            for domain_suffix in self.rules.domain_suffix
        )

        rules.extend(
            f"DOMAIN-KEYWORD,{domain_keyword}"
            for domain_keyword in self.rules.domain_keyword
        )

        rules.extend(f"IP-CIDR,{ip_cidr}" for ip_cidr in self.rules.ip_cidr)

        rules.extend(f"IP-CIDR6,{ip_cidr6}" for ip_cidr6 in self.rules.ip_cidr6)

        rules.extend(f"IP-ASN,{ip_asn}" for ip_asn in self.rules.ip_asn)

        rules.extend(f"USER-AGENT,{ua}" for ua in self.rules.ua)

        rules.extend(
            surge_logical_serialize(tree=tree, include=include_rule_types)
            for tree in self.rules.logical
        )

        rules.extend(f"URL-REGEX,{url_regex}" for url_regex in self.rules.url_regex)
        filtered_rules = list(filter(None, rules))
        content = "\n".join(filtered_rules)
        if content:
            return f"# Total: {len(filtered_rules)} rules\n{content}"
        return content
