import re
from collections.abc import Iterable
from typing import Self

from loguru import logger
from pydantic import BaseModel, Field

from .aho import Aho
from .enum import DomainType, ProcessingRuleType
from .logical import LogicalTree, output_sort_key
from .option import Option
from .trie import DomainTrie, IPTrie, IPTrie6


class SerializableRuleModel(BaseModel):
    domain: list[str] = []
    domain_suffix: list[str] = []
    domain_wildcard: list[str] = []
    domain_regex: list[str] = []
    domain_keyword: list[str] = []
    ip_cidr: list[str] = []
    ip_cidr6: list[str] = []
    ip_asn: list[str] = []
    logical: list[LogicalTree] = []
    process: list[str] = []
    user_agent: list[str] = []
    url_regex: list[str] = []


class RuleModel(BaseModel):
    domain_trie: DomainTrie = Field(default_factory=DomainTrie)
    domain_regex: set[str] = Field(default_factory=set)
    ip_trie: IPTrie = Field(default_factory=IPTrie)
    ip_trie6: IPTrie6 = Field(default_factory=IPTrie6)
    ip_asn: set[str] = Field(default_factory=set)
    logical: set[LogicalTree] = Field(default_factory=set)
    process: set[str] = Field(default_factory=set)
    user_agent: set[str] = Field(default_factory=set)
    domain_keyword: set[str] = Field(default_factory=set)
    url_regex: set[str] = Field(default_factory=set)

    def merge_with(self, other: Self) -> None:
        self.domain_trie.merge(other.domain_trie)
        self.domain_regex.update(other.domain_regex)
        self.domain_keyword.update(other.domain_keyword)
        self.ip_trie.merge(other.ip_trie)
        self.ip_trie6.merge(other.ip_trie6)
        self.ip_asn.update(other.ip_asn)
        self.logical.update(other.logical)
        self.process.update(other.process)
        self.user_agent.update(other.user_agent)
        self.url_regex.update(other.url_regex)

    @classmethod
    def merge_all(cls, models: Iterable[Self]) -> Self:
        """Merge models in order, reusing and returning the first one.

        The first model is mutated in place. The caller must own it and must
        not share it with other code.
        """
        iterator = iter(models)
        try:
            merged = next(iterator)
        except StopIteration:
            return cls()

        for model in iterator:
            merged.merge_with(model)
        return merged

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

    def _deduplicate_domain_regex(self) -> None:
        """Remove DOMAIN rules already matched by a DOMAIN_REGEX rule."""
        if not self.domain_regex:
            return
        regexes: list[tuple[str, re.Pattern[str]]] = []
        for domain_regex in self.domain_regex:
            try:
                regexes.append((domain_regex, re.compile(domain_regex)))
            except re.error as error:
                logger.error(f"Cannot compile DOMAIN_REGEX,{domain_regex}: {error}")

        for domain, domain_type in self.domain_trie.items():
            if domain_type != DomainType.DOMAIN:
                continue
            for domain_regex, regex in regexes:
                if regex.search(domain):
                    self.domain_trie.remove(domain)
                    logger.error(f"DOMAIN,{domain} -> DOMAIN-REGEX,{domain_regex}")
                    break

    def _remove_domains_of_type(self, domain_type: DomainType) -> None:
        for domain, current_domain_type in self.domain_trie.items():
            if current_domain_type == domain_type:
                self.domain_trie.remove(domain)

    def _remove_rules_of_type(self, rule_type: ProcessingRuleType) -> None:
        match rule_type:
            case ProcessingRuleType.DOMAIN:
                self._remove_domains_of_type(DomainType.DOMAIN)
            case ProcessingRuleType.DOMAIN_SUFFIX:
                self._remove_domains_of_type(DomainType.DOMAIN_SUFFIX)
            case ProcessingRuleType.DOMAIN_WILDCARD:
                self._remove_domains_of_type(DomainType.DOMAIN_WILDCARD)
            case ProcessingRuleType.DOMAIN_REGEX:
                self.domain_regex.clear()
            case ProcessingRuleType.DOMAIN_KEYWORD:
                self.domain_keyword.clear()
            case ProcessingRuleType.IP_CIDR:
                self.ip_trie = IPTrie()
            case ProcessingRuleType.IP_CIDR6:
                self.ip_trie6 = IPTrie6()
            case ProcessingRuleType.IP_ASN:
                self.ip_asn.clear()
            case ProcessingRuleType.LOGICAL:
                self.logical.clear()
            case ProcessingRuleType.PROCESS_NAME:
                self.process.clear()
            case ProcessingRuleType.USER_AGENT:
                self.user_agent.clear()
            case ProcessingRuleType.URL_REGEX:
                self.url_regex.clear()

    def filter(self, option: Option):
        """Apply various optimization and filtering rules to clean up and optimize the rule set."""
        processing = option.processing
        if processing.include_rule_types:
            included_rule_types = set(processing.include_rule_types)
            for rule_type in ProcessingRuleType:
                if rule_type not in included_rule_types:
                    self._remove_rules_of_type(rule_type)
        for rule_type in processing.exclude_rule_types:
            self._remove_rules_of_type(rule_type)
        for domain in option.processing.exclude_suffixes:
            self.domain_trie.filter_by_domain(domain)
        self.domain_trie.filter_by_wildcard()
        self.domain_keyword = set(
            filter(self._deduplicate_domain_keyword(), self.domain_keyword)
        )
        keywords = [*self.domain_keyword, *option.processing.exclude_keywords]
        if keywords:
            aho = Aho(keywords)
            for domain, domain_type in self.domain_trie.items():
                is_matched, keyword = aho.matched(domain)
                if is_matched:
                    self.domain_trie.remove(domain)
                    logger.error(f"{domain_type},{domain} -> DOMAIN-KEYWORD,{keyword}")
            for domain_regex in list(self.domain_regex):
                is_matched, keyword = aho.matched(domain_regex.replace(r"\.", "."))
                if is_matched:
                    self.domain_regex.remove(domain_regex)
                    logger.error(
                        f"DOMAIN_REGEX,{domain_regex} -> DOMAIN-KEYWORD,{keyword}"
                    )
        self._deduplicate_domain_regex()

    def to_serializable_rule_model(self) -> SerializableRuleModel:
        serializable_rule = SerializableRuleModel()
        for domain, domain_type in self.domain_trie.sorted_iteritems():
            if domain_type == DomainType.DOMAIN:
                serializable_rule.domain.append(domain)
            elif domain_type == DomainType.DOMAIN_SUFFIX:
                serializable_rule.domain_suffix.append(domain)
            elif domain_type == DomainType.DOMAIN_WILDCARD:
                serializable_rule.domain_wildcard.append(domain)
        serializable_rule.domain_regex.extend(sorted(self.domain_regex))
        serializable_rule.domain_keyword.extend(sorted(self.domain_keyword))
        serializable_rule.ip_cidr.extend(self.ip_trie.iteritems())
        serializable_rule.ip_cidr6.extend(self.ip_trie6.iteritems())
        serializable_rule.ip_asn.extend(sorted(self.ip_asn, key=int))
        serializable_rule.logical.extend(
            sorted(self.logical, key=lambda tree: output_sort_key(tree.root))
        )
        serializable_rule.process.extend(sorted(self.process))
        serializable_rule.user_agent.extend(sorted(self.user_agent))
        serializable_rule.url_regex.extend(sorted(self.url_regex))
        return serializable_rule


class V2rayDomainInclude(BaseModel):
    name: str
    include_attrs: list[str] = []
    exclude_attrs: list[str] = []


class V2rayDomainResult(BaseModel):
    rules: RuleModel = RuleModel()
    includes: list[V2rayDomainInclude] = []
