from typing import TypedDict, override

import yaml
from yaml import CDumper

from rule_set.models import Artifact, ArtifactKind, Option, SerializableRuleModel

from ..logic.clash import serialize as logical_serialize
from .base import BaseSerializer


class ClashPayload(TypedDict):
    payload: list[str]


class ClashSerializer(BaseSerializer):
    def __init__(self, *, rules: SerializableRuleModel, option: Option) -> None:
        super().__init__(rules=rules, option=option)
        self.serialized_logical_rules: list[str] = [
            serialized
            for tree in self.rules.logical
            if (serialized := logical_serialize(tree=tree)) is not None
        ]

    def domain(self) -> list[str]:
        payload: list[str] = []
        payload.extend(self.rules.domain)
        payload.extend(
            f"+.{domain_suffix}" for domain_suffix in self.rules.domain_suffix
        )
        return payload

    def ip_cidr(self) -> list[str]:
        payload: list[str] = []
        payload.extend(self.rules.ip_cidr)
        payload.extend(self.rules.ip_cidr6)
        return payload

    def classical(self) -> list[str]:
        payload: list[str] = []
        payload.extend(
            f"DOMAIN-WILDCARD,{domain_wildcard}"
            for domain_wildcard in self.rules.domain_wildcard
        )

        payload.extend(
            f"DOMAIN-REGEX,{domain_regex}" for domain_regex in self.rules.domain_regex
        )

        payload.extend(
            f"DOMAIN-KEYWORD,{domain_keyword}"
            for domain_keyword in self.rules.domain_keyword
        )

        payload.extend(
            f"IP-ASN,{ip_asn},no-resolve"
            if self.option.serialization.no_resolve
            else f"IP-ASN,{ip_asn}"
            for ip_asn in self.rules.ip_asn
        )

        payload.extend(f"PROCESS-NAME,{process}" for process in self.rules.process)

        payload.extend(self.serialized_logical_rules)
        return payload

    def _serialize_payload_lines(self, payload: list[str]) -> str:
        lines = "".join(f"- '{value}'\n" for value in payload)
        return self._with_header(payload, f"'payload':\n{lines}")

    def _serialize_payload_with_pyyaml(self, payload: list[str]) -> str:
        yaml_content = yaml.dump(
            ClashPayload(payload=payload),
            sort_keys=False,
            Dumper=CDumper,
            width=-1,
        )
        return self._with_header(payload, yaml_content)

    def _with_header(self, payload: list[str], content: str) -> str:
        return (
            f"# Total: {len(payload)} rules\n"
            f"# Last Updated: {self.last_updated}\n"
            f"{content}"
        )

    @override
    def serialize(self) -> list[Artifact]:
        payloads: list[Artifact] = []
        if domain_payload := self.domain():
            payloads.append(
                Artifact(
                    kind=ArtifactKind.DOMAIN,
                    data=self._serialize_payload_lines(domain_payload),
                )
            )
        if ip_cidr_payload := self.ip_cidr():
            payloads.append(
                Artifact(
                    kind=ArtifactKind.IPCIDR,
                    data=self._serialize_payload_lines(ip_cidr_payload),
                )
            )
        if classical_payload := self.classical():
            payloads.append(
                Artifact(
                    kind=ArtifactKind.CLASSICAL,
                    data=self._serialize_payload_with_pyyaml(classical_payload),
                )
            )
        return payloads
