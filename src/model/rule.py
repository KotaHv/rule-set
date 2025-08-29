from typing import Self

from pydantic import BaseModel, Field
from loguru import logger

from .enum import DomainType
from .option import Option
from .trie import DomainTrie, IPTrie, IPTrie6
from .aho import Aho
from .logical import LogicalTree
from serialize.logical import surge_logical_serialize


class SerializableRuleModel(BaseModel):
    domain: list[str] = []
    domain_suffix: list[str] = []
    domain_wildcard: list[str] = []
    domain_keyword: list[str] = []
    ip_cidr: list[str] = []
    ip_cidr6: list[str] = []
    ip_asn: list[str] = []
    logical: list[LogicalTree] = []
    process: list[str] = []
    ua: list[str] = []


class RuleModel(BaseModel):
    domain_trie: DomainTrie = Field(default_factory=DomainTrie)
    ip_trie: IPTrie = Field(default_factory=IPTrie)
    ip_trie6: IPTrie6 = Field(default_factory=IPTrie6)
    ip_asn: list[str] | set[str] = set()
    logical: list[LogicalTree] = []
    process: list[str] | set[str] = set()
    ua: list[str] | set[str] = set()
    domain_keyword: list[str] | set[str] = set()

    def merge_with(self, other: Self) -> None:
        self.domain_trie.merge(other.domain_trie)
        self.domain_keyword.update(other.domain_keyword)
        self.ip_trie.merge(other.ip_trie)
        self.ip_trie6.merge(other.ip_trie6)
        self.ip_asn.update(other.ip_asn)
        if other.logical:
            logical_rules = [
                surge_logical_serialize(tree=tree) for tree in self.logical
            ]
            for tree in other.logical:
                if surge_logical_serialize(tree=tree) not in logical_rules:
                    self.logical.append(tree)
        self.process.update(other.process)
        self.ua.update(other.ua)

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
            if rule_type == "ip_trie":
                setattr(self, rule_type, IPTrie())
            elif rule_type == "ip_trie6":
                setattr(self, rule_type, IPTrie6())
            elif rule_type == "domain_trie":
                setattr(self, rule_type, DomainTrie())
            else:
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

    def sort(self):
        for key in RuleModel.model_fields.keys():
            if key in ["domain_trie", "ip_trie", "ip_trie6"]:
                continue
            value = getattr(self, key)
            if key == "ip_asn":
                value = sorted(
                    value,
                    key=lambda x: int(x),
                )
            elif key == "logical":
                value = sorted(value, key=lambda x: surge_logical_serialize(tree=x))
            else:
                value = sorted(value)
            setattr(self, key, value)

    def to_serializable_rule_model(self) -> SerializableRuleModel:
        serializable_rule = SerializableRuleModel()
        for domain, domain_type in self.domain_trie.sorted_iteritems():
            if domain_type == DomainType.DOMAIN:
                serializable_rule.domain.append(domain)
            elif domain_type == DomainType.DOMAIN_SUFFIX:
                serializable_rule.domain_suffix.append(domain)
            elif domain_type == DomainType.DOMAIN_WILDCARD:
                serializable_rule.domain_wildcard.append(domain)
        serializable_rule.domain_keyword.extend(self.domain_keyword)
        serializable_rule.ip_cidr.extend(self.ip_trie.iteritems())
        serializable_rule.ip_cidr6.extend(self.ip_trie6.iteritems())
        serializable_rule.ip_asn.extend(self.ip_asn)
        serializable_rule.logical.extend(self.logical)
        serializable_rule.process.extend(self.process)
        serializable_rule.ua.extend(self.ua)
        return serializable_rule


class V2rayDomainResult(BaseModel):
    rules: RuleModel = RuleModel()
    includes: list[str] = []
