import json
from typing import override

from rule_set.models import SerializableRuleModel
from rule_set.models.sing_box import (
    SingBoxClientRule,
    SingBoxRule,
    SingBoxRuleSet,
)
from rule_set.utils import domain

from ..logic import sing_box_logical_serialize
from ..srs import encode_rule_set
from .base import BaseRuleSerializer, BaseSerializer


class SingBoxRuleSetSerializer(BaseRuleSerializer[SingBoxRuleSet]):
    @override
    def serialize(self, rules: SerializableRuleModel) -> SingBoxRuleSet:
        serialized_rules: list[SingBoxClientRule | SingBoxRule] = []

        rule: SingBoxClientRule = {}
        if rules.domain:
            rule["domain"] = rules.domain
        if rules.domain_suffix:
            rule["domain_suffix"] = rules.domain_suffix
        domain_regex = [
            *(domain.wildcard_to_regex(item) for item in rules.domain_wildcard),
            *rules.domain_regex,
        ]
        if domain_regex:
            rule["domain_regex"] = domain_regex
        if rules.domain_keyword:
            rule["domain_keyword"] = rules.domain_keyword
        if ip_cidr := [*rules.ip_cidr, *rules.ip_cidr6]:
            rule["ip_cidr"] = ip_cidr

        if rule:
            serialized_rules.append(rule)
        if rules.process:
            serialized_rules.append({"process_name": rules.process})
        for tree in rules.logical:
            if logical_rule := sing_box_logical_serialize(tree=tree):
                serialized_rules.append(logical_rule)

        return SingBoxRuleSet(version=2, rules=serialized_rules)


class SingBoxJsonSerializer(BaseSerializer[SingBoxRuleSet, str]):
    @override
    def serialize(self, rule_set: SingBoxRuleSet) -> str:
        return json.dumps(rule_set)


class SingBoxSrsSerializer(BaseSerializer[SingBoxRuleSet, bytes]):
    @override
    def serialize(self, rule_set: SingBoxRuleSet) -> bytes:
        return encode_rule_set(rule_set)
