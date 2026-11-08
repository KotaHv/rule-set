from dataclasses import dataclass
from typing import TypedDict, override

import yaml
from yaml import CDumper

from rule_set.errors import SerializerError
from rule_set.models import ArtifactKind, SerializableRuleModel

from ..logic.clash import serialize as logical_serialize
from ..mrs import encode_domain, encode_ipcidr
from .base import BaseRuleSerializer, BaseSerializer


class ClashPayloadData(TypedDict):
    payload: list[str]


@dataclass(frozen=True, slots=True)
class ClashPayload:
    kind: ArtifactKind
    rules: list[str]


class ClashPayloadSerializer(BaseRuleSerializer[list[ClashPayload]]):
    @override
    def serialize(self, rules: SerializableRuleModel) -> list[ClashPayload]:
        payloads: list[ClashPayload] = []
        if domain_payload := self._domain(rules):
            payloads.append(
                ClashPayload(kind=ArtifactKind.DOMAIN, rules=domain_payload)
            )
        if ip_cidr_payload := self._ip_cidr(rules):
            payloads.append(
                ClashPayload(kind=ArtifactKind.IPCIDR, rules=ip_cidr_payload)
            )
        if classical_payload := self._classical(rules):
            payloads.append(
                ClashPayload(kind=ArtifactKind.CLASSICAL, rules=classical_payload)
            )
        return payloads

    @staticmethod
    def _domain(rules: SerializableRuleModel) -> list[str]:
        payload: list[str] = []
        payload.extend(rules.domain)
        payload.extend(f"+.{domain_suffix}" for domain_suffix in rules.domain_suffix)
        return payload

    @staticmethod
    def _ip_cidr(rules: SerializableRuleModel) -> list[str]:
        payload: list[str] = []
        payload.extend(rules.ip_cidr)
        payload.extend(rules.ip_cidr6)
        return payload

    def _classical(self, rules: SerializableRuleModel) -> list[str]:
        payload: list[str] = []
        payload.extend(
            f"DOMAIN-WILDCARD,{domain_wildcard}"
            for domain_wildcard in rules.domain_wildcard
        )

        payload.extend(
            f"DOMAIN-REGEX,{domain_regex}" for domain_regex in rules.domain_regex
        )

        payload.extend(
            f"DOMAIN-KEYWORD,{domain_keyword}"
            for domain_keyword in rules.domain_keyword
        )

        payload.extend(
            f"IP-ASN,{ip_asn},no-resolve"
            if self.option.serialization.no_resolve
            else f"IP-ASN,{ip_asn}"
            for ip_asn in rules.ip_asn
        )

        payload.extend(f"PROCESS-NAME,{process}" for process in rules.process)

        payload.extend(
            serialized
            for tree in rules.logical
            if (serialized := logical_serialize(tree=tree)) is not None
        )
        return payload


class ClashYamlSerializer(BaseSerializer[ClashPayload, str]):
    def __init__(self, *, last_updated: str) -> None:
        self.last_updated: str = last_updated

    @override
    def serialize(self, payload: ClashPayload) -> str:
        if payload.kind == ArtifactKind.CLASSICAL:
            content = yaml.dump(
                ClashPayloadData(payload=payload.rules),
                sort_keys=False,
                Dumper=CDumper,
                width=-1,
            )
        else:
            lines = "".join(f"- '{value}'\n" for value in payload.rules)
            content = f"'payload':\n{lines}"
        return self._with_header(payload.rules, content)

    def _with_header(self, payload: list[str], content: str) -> str:
        return (
            f"# Total: {len(payload)} rules\n"
            f"# Last Updated: {self.last_updated}\n"
            f"{content}"
        )


class ClashMrsSerializer(BaseSerializer[ClashPayload, bytes]):
    @override
    def serialize(self, payload: ClashPayload) -> bytes:
        match payload.kind:
            case ArtifactKind.DOMAIN:
                return encode_domain(payload.rules)
            case ArtifactKind.IPCIDR:
                return encode_ipcidr(payload.rules)
            case _:
                raise SerializerError(
                    f"cannot encode {payload.kind} payload as an MRS rule set"
                )
