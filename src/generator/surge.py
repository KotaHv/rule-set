from loguru import logger

import logic_rule_proc
from model import RuleModel, SourceModel
from config import DIR_PATH

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


class SurgeGenerator:
    def __init__(self, *, info: SourceModel, rules: RuleModel) -> None:
        self.info = info
        self.rules = rules
        dir_path = DIR_PATH / "Surge"
        dir_path.mkdir(exist_ok=True)
        self.path = dir_path / (info.filename + ".list")

    def generate(self):
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
        if self.rules.domain_wildcard:
            rules.extend(
                [
                    f"DOMAIN-WILDCARD,{domain_wildcard}"
                    for domain_wildcard in self.rules.domain_wildcard
                ]
            )
        if self.info.no_resolve:
            if self.rules.ip_cidr:
                rules.extend(
                    [f"IP-CIDR,{ip_cidr},no-resolve" for ip_cidr in self.rules.ip_cidr]
                )
            if self.rules.ip_cidr6:
                rules.extend(
                    [
                        f"IP-CIDR6,{ip_cidr6},no-resolve"
                        for ip_cidr6 in self.rules.ip_cidr6
                    ]
                )
            if self.rules.ip_asn:
                rules.extend(
                    [f"IP-ASN,{ip_asn},no-resolve" for ip_asn in self.rules.ip_asn]
                )
        else:
            if self.rules.ip_cidr:
                rules.extend([f"IP-CIDR,{ip_cidr}" for ip_cidr in self.rules.ip_cidr])

            if self.rules.ip_cidr6:
                rules.extend(
                    [f"IP-CIDR6,{ip_cidr6}" for ip_cidr6 in self.rules.ip_cidr6]
                )
            if self.rules.ip_asn:
                rules.extend([f"IP-ASN,{ip_asn}" for ip_asn in self.rules.ip_asn])
        if self.rules.ua:
            rules.extend([f"USER-AGENT,{ua}" for ua in self.rules.ua])
        if self.rules.process:
            rules.extend([f"PROCESS-NAME,{process}" for process in self.rules.process])
        if self.rules.logical:
            rules.extend(
                [
                    logic_rule_proc.serialize(node=node, include=include_rule_types)
                    for node in self.rules.logical
                ]
            )
        content = "\n".join(filter(None, rules))
        if content:
            with self.path.open("w") as f:
                f.write(content)
            logger.success(f"{self.path} generated successfully")
