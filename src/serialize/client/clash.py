import yaml
from yaml import CDumper

from model import SerializableRuleModel, Option

from .base import BaseSerialize
from ..logical.clash import serialize as logical_serialize


ignore_types = ["ua", "logical"]


class Serialize(BaseSerialize):
    def __init__(self, *, rules: SerializableRuleModel, option: Option) -> None:
        super().__init__(rules=rules, option=option)
        self.serialized_logical_rules = list(
            filter(
                None,
                [logical_serialize(root_node=node) for node in self.rules.logical],
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

    def classical(self, skip_domain: bool = False, skip_ip_cidr: bool = False) -> list:
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
                f"DOMAIN-WILDCARD,{domain_wildcard}"
                for domain_wildcard in self.rules.domain_wildcard
            ]
        )

        payload.extend(
            [
                f"DOMAIN-KEYWORD,{domain_keyword}"
                for domain_keyword in self.rules.domain_keyword
            ]
        )
        if not skip_ip_cidr:
            payload.extend(
                [
                    f"IP-CIDR,{ip_cidr},no-resolve"
                    if self.option.serialization.no_resolve
                    else f"IP-CIDR,{ip_cidr}"
                    for ip_cidr in self.rules.ip_cidr
                ]
            )
            payload.extend(
                [
                    f"IP-CIDR6,{ip_cidr6},no-resolve"
                    if self.option.serialization.no_resolve
                    else f"IP-CIDR6,{ip_cidr6}"
                    for ip_cidr6 in self.rules.ip_cidr6
                ]
            )

        payload.extend(
            [
                f"IP-ASN,{ip_asn},no-resolve"
                if self.option.serialization.no_resolve
                else f"IP-ASN,{ip_asn}"
                for ip_asn in self.rules.ip_asn
            ]
        )

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
        if self.option.geo_ip.country_code is not None:
            return self._serialize_payload(self.ip_cidr(), "ipcidr", "'")
        payloads = []
        if domain_payload := self.domain():
            payloads.append(self._serialize_payload(domain_payload, "domain", "'"))
        if ip_cidr_payload := self.ip_cidr():
            payloads.append(self._serialize_payload(ip_cidr_payload, "ipcidr", "'"))
        if classical_payload := self.classical(skip_domain=True, skip_ip_cidr=True):
            payloads.append(
                self._serialize_payload(classical_payload, "classical", None)
            )
        return payloads
