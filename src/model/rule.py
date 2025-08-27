import ipaddress
from typing import Any, Self

from pydantic import BaseModel, Field, field_validator
from loguru import logger

from model.enum import DomainType

from .type import AnyTreeNode
from .option import Option
from .trie import DomainTrie
from .aho import Aho
from serialize.logical import surge_logical_serialize


class BaseRuleModel(BaseModel):
    ip_cidr: set[str] | list[str] = set()
    ip_cidr6: set[str] | list[str] = set()
    ip_asn: set[str] | list[str] = set()
    logical: list[AnyTreeNode] = []
    process: set[str] | list[str] = set()
    ua: set[str] | list[str] = set()
    domain_keyword: set[str] | list[str] = set()

    @field_validator("*", mode="before")
    def ensure_list(cls, v: Any) -> Any:
        if isinstance(v, set):
            return list(v)
        return v

    def merge_with(self, other: Self) -> None:
        self.domain_keyword.update(other.domain_keyword)
        self.ip_cidr.update(other.ip_cidr)
        self.ip_cidr6.update(other.ip_cidr6)
        self.ip_asn.update(other.ip_asn)
        if other.logical:
            node_list = [
                surge_logical_serialize(root_node=node) for node in self.logical
            ]
            for node in other.logical:
                if surge_logical_serialize(root_node=node) in node_list:
                    continue
                self.logical.append(node)
        self.process.update(other.process)
        self.ua.update(other.ua)


class RuleModel(BaseRuleModel):
    domain: set[str] | list[str] = set()
    domain_suffix: set[str] | list[str] = set()
    domain_wildcard: set[str] | list[str] = set()

    def merge_with(self, other: Self) -> None:
        self.domain.update(other.domain)
        self.domain_suffix.update(other.domain_suffix)
        self.domain_wildcard.update(other.domain_wildcard)
        super().merge_with(other)

    def sort(self):
        for key in RuleModel.model_fields.keys():
            value = getattr(self, key)
            if key == "ip_cidr":
                value = sorted(
                    value,
                    key=lambda x: ipaddress.IPv4Network(x).network_address,
                )
            elif key == "ip_cidr6":
                value = sorted(
                    value,
                    key=lambda x: ipaddress.IPv6Network(x).network_address,
                )
            elif key == "ip_asn":
                value = sorted(
                    value,
                    key=lambda x: int(x),
                )
            elif key == "logical":
                value = sorted(
                    value, key=lambda x: surge_logical_serialize(root_node=x)
                )
            else:
                value = sorted(value)
            setattr(self, key, value)

    def has_only_ip_cidr_rules(self, ignore_types: list = []) -> bool:
        return self._has_only_rules_of_type(["ip_cidr", "ip_cidr6"], ignore_types)

    def has_only_domain_rules(self, ignore_types: list = []) -> bool:
        return self._has_only_rules_of_type(["domain", "domain_suffix"], ignore_types)

    def _has_only_rules_of_type(
        self, allowed_types: list, ignore_types: list = []
    ) -> bool:
        rule_types = list(RuleModel.model_fields.keys())
        ignore_types = set(allowed_types + ignore_types)
        for rule_type in ignore_types:
            rule_types.remove(rule_type)
        for rule_type in rule_types:
            if getattr(self, rule_type):
                return False
        return any(getattr(self, rule_type) for rule_type in allowed_types)

    def count_rules(self, ignore_types: list = []) -> int:
        count = 0
        rule_types = list(RuleModel.model_fields.keys())
        for rule_type in ignore_types:
            rule_types.remove(rule_type)
        for rule_type in rule_types:
            count += len(getattr(self, rule_type))
        return count


class TrieRuleModel(BaseRuleModel):
    domain_trie: DomainTrie = Field(default_factory=DomainTrie)

    def merge_with(self, other: Self) -> None:
        self.domain_trie.merge(other.domain_trie)
        super().merge_with(other)

    def merge_with_rule_model(self, other: RuleModel) -> None:
        for domain in other.domain:
            self.domain_trie.add(domain, DomainType.DOMAIN)
        for domain_suffix in other.domain_suffix:
            self.domain_trie.add(domain_suffix, DomainType.DOMAIN_SUFFIX)
        for domain_wildcard in other.domain_wildcard:
            self.domain_trie.add(domain_wildcard, DomainType.DOMAIN_WILDCARD)
        super().merge_with(other)

    def _deduplicate_domain_keyword(self):
        """Remove domain-keyword rules that are already covered by shorter keywords."""
        aho = Aho(self.domain_keyword)

        def is_duplicate(keyword: str) -> bool:
            is_dup, covered_keyword = aho.is_duplicate(keyword)
            if is_dup:
                logger.error(
                    f"DOMAIN-KEYWORD,{keyword} -> DOMAIN-KEYWORD,{covered_keyword}"
                )
                return False
            return True

        return is_duplicate

    def filter(self, option: Option):
        """Apply various optimization and filtering rules to clean up and optimize the rule set."""
        for rule_type in option.processing.exclude_rule_types:
            setattr(self, rule_type, set())
        for domain in option.processing.exclude_suffixes:
            self.domain_trie.filter_by_domain(domain)
        self.domain_keyword = set(
            filter(self._deduplicate_domain_keyword(), self.domain_keyword)
        )
        keywords = list(self.domain_keyword)
        keywords.extend(option.processing.exclude_keywords)
        if keywords:
            aho = Aho(keywords)
            for domain, domain_type in self.domain_trie.items():
                is_matched, keyword = aho.matched(domain)
                if is_matched:
                    self.domain_trie.remove(domain)
                    logger.error(f"{domain_type},{domain} -> DOMAIN-KEYWORD,{keyword}")

    def to_rule_model(self) -> RuleModel:
        rule_model = RuleModel()
        for domain, domain_type in self.domain_trie.sorted_iteritems():
            if domain_type == DomainType.DOMAIN:
                rule_model.domain.add(domain)
            elif domain_type == DomainType.DOMAIN_SUFFIX:
                rule_model.domain_suffix.add(domain)
            elif domain_type == DomainType.DOMAIN_WILDCARD:
                rule_model.domain_wildcard.add(domain)
        rule_model.domain_keyword.update(self.domain_keyword)
        rule_model.ip_cidr.update(self.ip_cidr)
        rule_model.ip_cidr6.update(self.ip_cidr6)
        rule_model.ip_asn.update(self.ip_asn)
        rule_model.logical.extend(self.logical)
        rule_model.process.update(self.process)
        rule_model.ua.update(self.ua)
        return rule_model


class V2rayDomainResult(BaseModel):
    rules: TrieRuleModel = TrieRuleModel()
    includes: list[str] = []
