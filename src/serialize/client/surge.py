from .base import BaseSerialize
from ..logical import surge_logical_serialize
from utils.domain import regex_to_wildcard


include_rule_types = [
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-SET",
    "DOMAIN-WILDCARD",
    "IP-CIDR",
    "IP-CIDR6",
    "GEOIP",
    "IP-ASN",
    "USER-AGENT",
    "URL-REGEX",
    "PROCESS-NAME",
    "SUBNET",
    "DEST-PORT",
    "IN-PORT",
    "SRC-PORT",
    "SRC-IP",
    "PROTOCOL",
    "SCRIPT",
    "CELLULAR-RADIO",
    "DEVICE-NAME",
    "RULE-SET",
]


class Serialize(BaseSerialize):
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

        rules.extend(
            f"DOMAIN-WILDCARD,{domain_wildcard}"
            for domain_wildcard in self.rules.domain_wildcard
        )

        rules.extend(
            f"IP-CIDR,{ip_cidr},no-resolve"
            if self.option.serialization.no_resolve
            else f"IP-CIDR,{ip_cidr}"
            for ip_cidr in self.rules.ip_cidr
        )

        rules.extend(
            f"IP-CIDR6,{ip_cidr6},no-resolve"
            if self.option.serialization.no_resolve
            else f"IP-CIDR6,{ip_cidr6}"
            for ip_cidr6 in self.rules.ip_cidr6
        )

        rules.extend(
            f"IP-ASN,{ip_asn},no-resolve"
            if self.option.serialization.no_resolve
            else f"IP-ASN,{ip_asn}"
            for ip_asn in self.rules.ip_asn
        )

        rules.extend(f"USER-AGENT,{ua}" for ua in self.rules.ua)

        rules.extend(f"PROCESS-NAME,{process}" for process in self.rules.process)

        rules.extend(
            surge_logical_serialize(tree=tree, include=include_rule_types)
            for tree in self.rules.logical
        )

        rules.extend(f"URL-REGEX,{url_regex}" for url_regex in self.rules.url_regex)
        rules.extend(
            f"DOMAIN-WILDCARD,{w}"
            for domain_regex in self.rules.domain_regexp
            for w in regex_to_wildcard(domain_regex)
        )
        filtered_rules = list(filter(None, rules))
        content = "\n".join(filtered_rules)
        if content:
            return f"# Total: {len(filtered_rules)} rules\n{content}"
        return content
