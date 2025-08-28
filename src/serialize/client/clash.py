import yaml
from yaml import CDumper

from model import SerializableRuleModel, Option

from .base import BaseSerialize
from ..logical import surge_logical_serialize


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

ignore_types = ["domain_wildcard", "ua", "logical"]


class Serialize(BaseSerialize):
    def __init__(self, *, rules: SerializableRuleModel, option: Option) -> None:
        super().__init__(rules=rules, option=option)
        self.serialized_logical_rules = list(
            filter(
                None,
                [
                    surge_logical_serialize(root_node=node, include=include_rule_types)
                    for node in self.rules.logical
                ],
            )
        )

    def domain(self) -> list:
        payload = []
        payload.extend(self.rules.domain)
        payload.extend(
            [f"+.{domain_suffix}" for domain_suffix in self.rules.domain_suffix]
        )
        return payload

    def ip_cidr(self) -> list:
        payload = []
        payload.extend(self.rules.ip_cidr)
        payload.extend(self.rules.ip_cidr6)
        return payload

    def classical(self, skip_domain: bool = False) -> list:
        payload = []
        if not skip_domain:
            payload.extend([f"DOMAIN,{domain}" for domain in self.rules.domain])
            payload.extend(
                [
                    f"DOMAIN-SUFFIX,{domain_suffix}"
                    for domain_suffix in self.rules.domain_suffix
                ]
            )

        payload.extend(
            [
                f"DOMAIN-KEYWORD,{domain_keyword}"
                for domain_keyword in self.rules.domain_keyword
            ]
        )
        if self.option.serialization.no_resolve:
            payload.extend(
                [f"IP-CIDR,{ip_cidr},no-resolve" for ip_cidr in self.rules.ip_cidr]
            )
            payload.extend(
                [f"IP-CIDR6,{ip_cidr6},no-resolve" for ip_cidr6 in self.rules.ip_cidr6]
            )
            payload.extend(
                [f"IP-ASN,{ip_asn},no-resolve" for ip_asn in self.rules.ip_asn]
            )
        else:
            payload.extend([f"IP-CIDR,{ip_cidr}" for ip_cidr in self.rules.ip_cidr])

            payload.extend([f"IP-CIDR6,{ip_cidr6}" for ip_cidr6 in self.rules.ip_cidr6])

            payload.extend([f"IP-ASN,{ip_asn}" for ip_asn in self.rules.ip_asn])

        payload.extend([f"PROCESS-NAME,{process}" for process in self.rules.process])

        payload.extend(self.serialized_logical_rules)
        return payload

    def _serialize_payload(
        self, payload: str, behavior: str, style: str
    ) -> tuple[str, str]:
        yaml_content = yaml.dump(
            {"payload": payload},
            sort_keys=False,
            Dumper=CDumper,
            width=-1,
            default_style=style,
        )
        # Add rule count comment for clash format
        rule_count = len(payload)
        comment = f"# Total: {rule_count} rules\n"
        return (
            behavior,
            comment + yaml_content,
        )

    def serialize(self) -> tuple[str, str] | list[tuple[str, str]]:
        if self.option.serialization.clash_optimize:
            if not self.serialized_logical_rules:
                if self.has_only_domain_rules(ignore_types):
                    return self._serialize_payload(self.domain(), "domain", "'")
                if self.has_only_ip_cidr_rules(ignore_types):
                    return self._serialize_payload(self.ip_cidr(), "ipcidr", "'")
            if (
                self.count_rules(ignore_types) + len(self.serialized_logical_rules)
                > 10000
            ):
                domain_payload = self.domain()
                classical_payload = self.classical(skip_domain=True)
                return [
                    self._serialize_payload(domain_payload, "domain", "'"),
                    self._serialize_payload(classical_payload, "classical", None),
                ]

        payload = self.classical()
        if payload:
            return self._serialize_payload(payload, "classical", None)

        return ""

    def has_only_ip_cidr_rules(self, ignore_types: list = []) -> bool:
        return self._has_only_rule_types(["ip_cidr", "ip_cidr6"], ignore_types)

    def has_only_domain_rules(self, ignore_types: list = []) -> bool:
        return self._has_only_rule_types(["domain", "domain_suffix"], ignore_types)

    def _has_only_rule_types(
        self, allowed_types: list, ignore_types: list = []
    ) -> bool:
        rule_types = list(SerializableRuleModel.model_fields.keys())
        ignore_types = set(allowed_types + ignore_types)
        for rule_type in rule_types:
            if rule_type in ignore_types:
                continue
            if getattr(self.rules, rule_type):
                return False
        return any(getattr(self.rules, rule_type) for rule_type in allowed_types)

    def count_rules(self, ignore_types: list = []) -> int:
        count = 0
        rule_types = list(SerializableRuleModel.model_fields.keys())
        for rule_type in rule_types:
            if rule_type in ignore_types:
                continue
            count += len(getattr(self.rules, rule_type))
        return count
