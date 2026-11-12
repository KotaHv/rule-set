import ipaddress
import re
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import ClassVar, Self

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from .aho import Aho
from .enum import DomainType, ProcessingRuleType
from .logical import LogicalTree, output_sort_key
from .option import Option
from .resource import V2rayDomainResource
from .trie import DomainTrie, IPTrie, IPTrie6


@dataclass
class SerializableRuleModel:
    domain: list[str] = dataclass_field(default_factory=list)
    domain_suffix: list[str] = dataclass_field(default_factory=list)
    domain_wildcard: list[str] = dataclass_field(default_factory=list)
    domain_regex: list[str] = dataclass_field(default_factory=list)
    domain_keyword: list[str] = dataclass_field(default_factory=list)
    ip_cidr: list[str] = dataclass_field(default_factory=list)
    ip_cidr6: list[str] = dataclass_field(default_factory=list)
    ip_asn: list[str] = dataclass_field(default_factory=list)
    logical: list[LogicalTree] = dataclass_field(default_factory=list)
    process: list[str] = dataclass_field(default_factory=list)
    user_agent: list[str] = dataclass_field(default_factory=list)
    url_regex: list[str] = dataclass_field(default_factory=list)


def _domain_sort_key(domain: str) -> tuple[str, ...]:
    return tuple(domain.split(".")[::-1])


def _ipv4_sort_key(ip_cidr: str) -> ipaddress.IPv4Address:
    return ipaddress.IPv4Network(ip_cidr).network_address


def _ipv6_sort_key(ip_cidr: str) -> ipaddress.IPv6Address:
    return ipaddress.IPv6Network(ip_cidr).network_address


class RuleModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    domain: set[str] = Field(default_factory=set)
    domain_suffix: set[str] = Field(default_factory=set)
    domain_wildcard: set[str] = Field(default_factory=set)
    domain_regex: set[str] = Field(default_factory=set)
    domain_keyword: set[str] = Field(default_factory=set)
    ip_cidr: set[str] = Field(default_factory=set)
    ip_cidr6: set[str] = Field(default_factory=set)
    ip_asn: set[str] = Field(default_factory=set)
    logical: set[LogicalTree] = Field(default_factory=set)
    process: set[str] = Field(default_factory=set)
    user_agent: set[str] = Field(default_factory=set)
    url_regex: set[str] = Field(default_factory=set)

    def merge_with(self, other: Self) -> None:
        self.domain.update(other.domain)
        self.domain_suffix.update(other.domain_suffix)
        self.domain_wildcard.update(other.domain_wildcard)
        self.domain_regex.update(other.domain_regex)
        self.domain_keyword.update(other.domain_keyword)
        self.ip_cidr.update(other.ip_cidr)
        self.ip_cidr6.update(other.ip_cidr6)
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

        for domain in list(self.domain):
            for domain_regex, regex in regexes:
                if regex.search(domain):
                    self.domain.remove(domain)
                    logger.error(f"DOMAIN,{domain} -> DOMAIN-REGEX,{domain_regex}")
                    break

    def _remove_rules_of_type(self, rule_type: ProcessingRuleType) -> None:
        match rule_type:
            case ProcessingRuleType.DOMAIN:
                self.domain.clear()
            case ProcessingRuleType.DOMAIN_SUFFIX:
                self.domain_suffix.clear()
            case ProcessingRuleType.DOMAIN_WILDCARD:
                self.domain_wildcard.clear()
            case ProcessingRuleType.DOMAIN_REGEX:
                self.domain_regex.clear()
            case ProcessingRuleType.DOMAIN_KEYWORD:
                self.domain_keyword.clear()
            case ProcessingRuleType.IP_CIDR:
                self.ip_cidr.clear()
            case ProcessingRuleType.IP_CIDR6:
                self.ip_cidr6.clear()
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

    def _filter_keywords(self, exclude_keywords: list[str]) -> None:
        self.domain_keyword = set(
            filter(self._deduplicate_domain_keyword(), self.domain_keyword)
        )
        keywords = [*self.domain_keyword, *exclude_keywords]
        if not keywords:
            return
        aho = Aho(keywords)
        for domain_type, domains in (
            (DomainType.DOMAIN, self.domain),
            (DomainType.DOMAIN_SUFFIX, self.domain_suffix),
            (DomainType.DOMAIN_WILDCARD, self.domain_wildcard),
        ):
            for domain in list(domains):
                is_matched, keyword = aho.matched(domain)
                if is_matched:
                    domains.remove(domain)
                    logger.error(f"{domain_type},{domain} -> DOMAIN-KEYWORD,{keyword}")
        for domain_regex in list(self.domain_regex):
            is_matched, keyword = aho.matched(domain_regex.replace(r"\.", "."))
            if is_matched:
                self.domain_regex.remove(domain_regex)
                logger.error(f"DOMAIN_REGEX,{domain_regex} -> DOMAIN-KEYWORD,{keyword}")

    def _deduplicate_domains(self, exclude_suffixes: list[str]) -> None:
        domain_trie = DomainTrie()
        for domain in self.domain:
            domain_trie.add(domain, DomainType.DOMAIN)
        for domain in self.domain_suffix:
            domain_trie.add(domain, DomainType.DOMAIN_SUFFIX)
        for domain in self.domain_wildcard:
            domain_trie.add(domain, DomainType.DOMAIN_WILDCARD)
        for suffix in exclude_suffixes:
            domain_trie.filter_by_domain(suffix)
        domain_trie.filter_by_wildcard()

        self.domain.clear()
        self.domain_suffix.clear()
        self.domain_wildcard.clear()
        for domain, domain_type in domain_trie.iteritems():
            match domain_type:
                case DomainType.DOMAIN:
                    self.domain.add(domain)
                case DomainType.DOMAIN_SUFFIX:
                    self.domain_suffix.add(domain)
                case DomainType.DOMAIN_WILDCARD:
                    self.domain_wildcard.add(domain)

    @staticmethod
    def _deduplicate_ip_cidrs(
        ip_cidrs: set[str], ip_trie_type: type[IPTrie] | type[IPTrie6]
    ) -> set[str]:
        ip_trie = ip_trie_type()
        for ip_cidr in ip_cidrs:
            ip_trie.add(ipaddress.ip_network(ip_cidr, strict=False))
        return set(ip_trie.iteritems())

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
        self._filter_keywords(processing.exclude_keywords)
        self._deduplicate_domain_regex()
        self._deduplicate_domains(processing.exclude_suffixes)
        self.ip_cidr = self._deduplicate_ip_cidrs(self.ip_cidr, IPTrie)
        self.ip_cidr6 = self._deduplicate_ip_cidrs(self.ip_cidr6, IPTrie6)

    def to_serializable_rule_model(self) -> SerializableRuleModel:
        return SerializableRuleModel(
            domain=sorted(self.domain, key=_domain_sort_key),
            domain_suffix=sorted(self.domain_suffix, key=_domain_sort_key),
            domain_wildcard=sorted(self.domain_wildcard, key=_domain_sort_key),
            domain_regex=sorted(self.domain_regex),
            domain_keyword=sorted(self.domain_keyword),
            ip_cidr=sorted(self.ip_cidr, key=_ipv4_sort_key),
            ip_cidr6=sorted(self.ip_cidr6, key=_ipv6_sort_key),
            ip_asn=sorted(self.ip_asn, key=int),
            logical=sorted(self.logical, key=lambda tree: output_sort_key(tree.root)),
            process=sorted(self.process),
            user_agent=sorted(self.user_agent),
            url_regex=sorted(self.url_regex),
        )


class V2rayDomainResult(BaseModel):
    rules: RuleModel = RuleModel()
    resources: list[V2rayDomainResource] = []
