import re
import ipaddress
from collections import defaultdict
from typing import Any

from pydantic import BaseModel, field_validator
from loguru import logger

from .type import AnyTreeNode
from .option import Option
from utils import is_eTLD
from serialize.logical import surge_logical_serialize


class RuleModel(BaseModel):
    domain: set[str] | list[str] = set()
    domain_suffix: set[str] | list[str] = set()
    domain_keyword: set[str] | list[str] = set()
    domain_wildcard: set[str] | list[str] = set()
    ip_cidr: set[str] | list[str] = set()
    ip_cidr6: set[str] | list[str] = set()
    ip_asn: set[str] | list[str] = set()
    logical: list[AnyTreeNode] = []
    process: set[str] | list[str] = set()
    ua: set[str] | list[str] = set()

    @field_validator("*", mode="before")
    def ensure_list(cls, v: Any) -> Any:
        if isinstance(v, set):
            return list(v)
        return v

    def merge_with(self, other: "RuleModel") -> None:
        self.domain.update(other.domain)
        self.domain_suffix.update(other.domain_suffix)
        self.domain_keyword.update(other.domain_keyword)
        self.domain_wildcard.update(other.domain_wildcard)
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

    def _deduplicate_domain(self, domain: str):
        """Remove domains that are already covered by domain-suffix rules."""
        domain_parts = domain.split(".")
        suffixes_to_check = [
            ".".join(domain_parts[i:]) for i in range(len(domain_parts))
        ]
        for suffix in suffixes_to_check:
            if suffix in self.domain_suffix:
                logger.error(f"DOMAIN,{domain} -> DOMAIN-SUFFIX,{suffix}")
                return False
        return True

    def _deduplicate_domain_suffix(self, domain_suffix: str):
        """Remove domain-suffix rules that are already covered by shorter suffixes."""
        domain_suffix_parts = domain_suffix.split(".")
        suffixes_to_check = [
            ".".join(domain_suffix_parts[i:])
            for i in range(1, len(domain_suffix_parts))
        ]
        for suffix in suffixes_to_check:
            if suffix in self.domain_suffix:
                logger.error(f"DOMAIN-SUFFIX,{domain_suffix} -> DOMAIN-SUFFIX,{suffix}")
                return False
        return True

    def _deduplicate_domain_suffix_by_keyword(self, domain_suffix: str):
        """Remove domain-suffix rules that are already covered by domain-keyword rules."""
        for keyword in self.domain_keyword:
            if keyword in domain_suffix:
                logger.error(
                    f"DOMAIN-SUFFIX,{domain_suffix} -> DOMAIN-KEYWORD,{keyword}"
                )
                return False
        return True

    def _deduplicate_domain_keyword(self, candidate_keyword: str):
        """Remove domain-keyword rules that are already covered by shorter keywords."""
        for current_keyword in self.domain_keyword:
            if (
                current_keyword != candidate_keyword
                and current_keyword in candidate_keyword
            ):
                logger.error(
                    f"DOMAIN-KEYWORD,{candidate_keyword} -> DOMAIN-KEYWORD,{current_keyword}"
                )
                return False
        return True

    def _optimize_domains(self, exclude_optimized_domains: list[str] = []):
        """
        Optimize domains by converting them to domain-suffix rules and aggregating common suffixes.

        """
        for domain in self.domain:
            domain_parts = domain.split(".")
            for index in range(len(domain_parts) - 1, -1, -1):
                current_suffix = ".".join(domain_parts[index:])
                if is_eTLD(current_suffix):
                    continue
                logger.error(f"DOMAIN,{domain} -> DOMAIN-SUFFIX,{current_suffix}")
                self.domain_suffix.add(current_suffix)
                break
        self.domain.clear()
        domain_suffix_count = defaultdict(int)
        for domain_suffix in self.domain_suffix:
            domain_suffix_parts = domain_suffix.split(".")
            if len(domain_suffix) <= 2:
                continue
            for index in range(len(domain_suffix_parts) - 2, 0, -1):
                current_suffix = ".".join(domain_suffix_parts[index:])
                if is_eTLD(current_suffix):
                    continue
                if current_suffix in self.domain_suffix:
                    break
                domain_suffix_count[current_suffix] += 1
        for domain_suffix, count in domain_suffix_count.items():
            if count > 1 and domain_suffix not in exclude_optimized_domains:
                logger.error(domain_suffix)
                if isinstance(self.domain_suffix, set):
                    self.domain_suffix.add(domain_suffix)
                elif isinstance(self.domain_suffix, list):
                    self.domain_suffix.append(domain_suffix)

    def _exclude_domains_by_keywords(self, exclude_keywords: list[str]):
        escaped_keywords = map(re.escape, exclude_keywords)
        pattern = re.compile(f"({'|'.join(escaped_keywords)})")

        self.domain = {d for d in self.domain if not pattern.search(d)}
        self.domain_suffix = {d for d in self.domain_suffix if not pattern.search(d)}
        self.domain_wildcard = {
            d for d in self.domain_wildcard if not pattern.search(d)
        }

    def _exclude_domains_by_suffixes(self, exclude_suffixes: list[str]):
        escaped_suffixes = map(re.escape, exclude_suffixes)
        pattern = re.compile(f"({'|'.join(escaped_suffixes)})$")

        self.domain = {d for d in self.domain if not pattern.search(d)}
        self.domain_suffix = {d for d in self.domain_suffix if not pattern.search(d)}
        self.domain_wildcard = {
            d for d in self.domain_wildcard if not pattern.search(d)
        }

    def filter(self, option: Option):
        """Apply various optimization and filtering rules to clean up and optimize the rule set."""
        for rule_type in option.processing.exclude_rule_types:
            setattr(self, rule_type, set())
        self.domain = set(filter(self._deduplicate_domain, self.domain))
        self.domain_keyword = set(
            filter(self._deduplicate_domain_keyword, self.domain_keyword)
        )
        self.domain_suffix = set(
            filter(self._deduplicate_domain_suffix_by_keyword, self.domain_suffix)
        )
        self.domain_suffix = set(
            filter(self._deduplicate_domain_suffix, self.domain_suffix)
        )
        if option.processing.optimize_domains:
            self._optimize_domains(option.processing.exclude_optimized_domains)
        if option.processing.exclude_keywords:
            self._exclude_domains_by_keywords(option.processing.exclude_keywords)
        if option.processing.exclude_suffixes:
            self._exclude_domains_by_suffixes(option.processing.exclude_suffixes)

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


class V2rayDomainResult(BaseModel):
    rules: RuleModel = RuleModel()
    includes: list[str] = []
