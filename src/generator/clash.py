import yaml

from yaml import CDumper
from loguru import logger

import logic_rule_proc
from model import RuleModel, SourceModel
from config import DIR_PATH

include_rule_types = [
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-REGEX",
    "GEOSITE",
    "IP-CIDR",
    "IP-CIDR6",
    "IP-SUFFIX",
    "IP-ASN",
    "GEOIP",
    "SRC-GEOIP",
    "SRC-IP-ASN",
    "SRC-IP-CIDR",
    "SRC-IP-SUFFIX",
    "DST-PORT",
    "SRC-PORT",
    "IN-PORT",
    "IN-TYPE",
    "IN-USER",
    "IN-NAME",
    "PROCESS-PATH",
    "PROCESS-PATH-REGEX",
    "PROCESS-NAME",
    "PROCESS-NAME-REGEX",
    "UID",
    "NETWORK",
    "DSCP",
    "RULE-SET",
]


class ClashGenerator:
    def __init__(self, *, info: SourceModel, rules: RuleModel) -> None:
        self.info = info
        self.rules = rules
        dir_path = DIR_PATH / "Clash"
        self.path = dir_path / info.target_name.with_suffix(".yaml")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def generate(self):
        payload = []
        if self.rules.domain:
            payload.extend([f"DOMAIN,{domain}" for domain in self.rules.domain])
        if self.rules.domain_suffix:
            payload.extend(
                [
                    f"DOMAIN-SUFFIX,{domain_suffix}"
                    for domain_suffix in self.rules.domain_suffix
                ]
            )

        if self.rules.domain_keyword:
            payload.extend(
                [
                    f"DOMAIN-KEYWORD,{domain_keyword}"
                    for domain_keyword in self.rules.domain_keyword
                ]
            )
        if self.info.no_resolve:
            if self.rules.ip_cidr:
                payload.extend(
                    [f"IP-CIDR,{ip_cidr},no-resolve" for ip_cidr in self.rules.ip_cidr]
                )
            if self.rules.ip_cidr6:
                payload.extend(
                    [
                        f"IP-CIDR6,{ip_cidr6},no-resolve"
                        for ip_cidr6 in self.rules.ip_cidr6
                    ]
                )
            if self.rules.ip_asn:
                payload.extend(
                    [f"IP-ASN,{ip_asn},no-resolve" for ip_asn in self.rules.ip_asn]
                )
        else:
            if self.rules.ip_cidr:
                payload.extend([f"IP-CIDR,{ip_cidr}" for ip_cidr in self.rules.ip_cidr])
            if self.rules.ip_cidr6:
                payload.extend(
                    [f"IP-CIDR6,{ip_cidr6}" for ip_cidr6 in self.rules.ip_cidr6]
                )
            if self.rules.ip_asn:
                payload.extend([f"IP-ASN,{ip_asn}" for ip_asn in self.rules.ip_asn])
        if self.rules.process:
            payload.extend(
                [f"PROCESS-NAME,{process}" for process in self.rules.process]
            )
        if self.rules.logical:
            payload.extend(
                filter(
                    None,
                    [
                        logic_rule_proc.serialize(node=node, include=include_rule_types)
                        for node in self.rules.logical
                    ],
                )
            )
        if payload:
            with self.path.open("w") as f:
                yaml.dump(
                    {"payload": payload},
                    f,
                    sort_keys=False,
                    Dumper=CDumper,
                    width=-1,
                )
            logger.success(f"{self.path} generated successfully")
