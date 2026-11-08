from typing import NotRequired, Required, TypedDict, override

import yaml
from yaml import CDumper

from rule_set.models import SerializableRuleModel

from ..logic.egern import LogicalSetName, TaggedMapping
from ..logic.egern import serialize as logical_serialize
from .base import BaseRuleSerializer


class EgernDumper(CDumper):
    pass


class EgernTaggedMappingFields(TypedDict):
    match: str | TaggedMapping | list[TaggedMapping]
    no_resolve: NotRequired[bool]


def _represent_tagged_mapping(dumper: EgernDumper, value: TaggedMapping):
    fields: EgernTaggedMappingFields = {"match": value.match}
    if value.no_resolve:
        fields["no_resolve"] = True
    return dumper.represent_mapping(value.tag, fields)


EgernDumper.add_representer(TaggedMapping, _represent_tagged_mapping)

type LogicalSetValue = TaggedMapping | list[TaggedMapping]


class EgernConfig(TypedDict, total=False):
    no_resolve: Required[bool]
    domain_set: list[str]
    domain_suffix_set: list[str]
    domain_wildcard_set: list[str]
    domain_regex_set: list[str]
    domain_keyword_set: list[str]
    ip_cidr_set: list[str]
    ip_cidr6_set: list[str]
    asn_set: list[str]
    and_set: list[LogicalSetValue]
    or_set: list[LogicalSetValue]
    not_set: list[LogicalSetValue]
    url_regex_set: list[str]


class EgernSerializer(BaseRuleSerializer[str]):
    @override
    def serialize(self, rules: SerializableRuleModel) -> str:
        yaml_data: EgernConfig = {"no_resolve": self.option.serialization.no_resolve}
        rule_count = 0
        if rules.domain:
            yaml_data["domain_set"] = rules.domain
            rule_count += len(rules.domain)
        if rules.domain_suffix:
            yaml_data["domain_suffix_set"] = rules.domain_suffix
            rule_count += len(rules.domain_suffix)
        if rules.domain_wildcard:
            yaml_data["domain_wildcard_set"] = rules.domain_wildcard
            rule_count += len(rules.domain_wildcard)
        if rules.domain_regex:
            yaml_data["domain_regex_set"] = rules.domain_regex
            rule_count += len(rules.domain_regex)
        if rules.domain_keyword:
            yaml_data["domain_keyword_set"] = rules.domain_keyword
            rule_count += len(rules.domain_keyword)
        if rules.ip_cidr:
            yaml_data["ip_cidr_set"] = rules.ip_cidr
            rule_count += len(rules.ip_cidr)
        if rules.ip_cidr6:
            yaml_data["ip_cidr6_set"] = rules.ip_cidr6
            rule_count += len(rules.ip_cidr6)
        if rules.ip_asn:
            yaml_data["asn_set"] = rules.ip_asn
            rule_count += len(rules.ip_asn)
        if rules.logical:
            logical_sets: dict[LogicalSetName, list[LogicalSetValue]] = {}
            for rule in rules.logical:
                if result := logical_serialize(tree=rule):
                    logical_set, item = result
                    logical_sets.setdefault(logical_set, []).append(item)
            for logical_set, items in logical_sets.items():
                yaml_data[logical_set] = items
                rule_count += len(items)
        if rules.url_regex:
            yaml_data["url_regex_set"] = rules.url_regex
            rule_count += len(rules.url_regex)
        if len(yaml_data.keys()) > 1:
            yaml_content = yaml.dump(yaml_data, sort_keys=False, Dumper=EgernDumper)
            if rule_count > 0:
                yaml_content = f"# Total: {rule_count} rules\n# Last Updated: {self.last_updated}\n{yaml_content}"
            return yaml_content
        return ""
