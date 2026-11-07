import json
from typing import override

from rule_set.models import Artifact, ArtifactKind
from rule_set.models.sing_box import (
    SingBoxClientRule,
    SingBoxConfig,
    SingBoxRule,
)
from rule_set.utils import domain

from ..logic import sing_box_logical_serialize
from .base import BaseSerializer


class SingBoxSerializer(BaseSerializer):
    @override
    def serialize(self) -> list[Artifact]:
        rules: list[SingBoxClientRule | SingBoxRule] = []

        rule: SingBoxClientRule = {}
        if self.rules.domain:
            rule["domain"] = self.rules.domain
        if self.rules.domain_suffix:
            rule["domain_suffix"] = self.rules.domain_suffix
        domain_regex = [
            *(domain.wildcard_to_regex(item) for item in self.rules.domain_wildcard),
            *self.rules.domain_regex,
        ]
        if domain_regex:
            rule["domain_regex"] = domain_regex
        if self.rules.domain_keyword:
            rule["domain_keyword"] = self.rules.domain_keyword
        if ip_cidr := [*self.rules.ip_cidr, *self.rules.ip_cidr6]:
            rule["ip_cidr"] = ip_cidr

        if rule:
            rules.append(rule)
        if self.rules.process:
            rules.append({"process_name": self.rules.process})
        for tree in self.rules.logical:
            if logical_rule := sing_box_logical_serialize(tree=tree):
                rules.append(logical_rule)

        if not rules:
            return [Artifact(kind=ArtifactKind.DEFAULT, data="")]

        return [
            Artifact(
                kind=ArtifactKind.DEFAULT,
                data=json.dumps(SingBoxConfig(version=2, rules=rules)),
            )
        ]
