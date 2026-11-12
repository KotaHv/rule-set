# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnannotatedClassAttribute=false
import ipaddress
import re
from collections.abc import Iterator
from typing import ClassVar, Self, override

from loguru import logger
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema
from pygtrie import Trie
from pytricia import PyTricia

from ..utils.domain import wildcard_to_regex
from .enum import DomainType


class DomainTrie:
    def __init__(self):
        self._trie: Trie[tuple[str, ...], DomainType, str] = Trie()
        self._seen_wildcard: bool = False

    def _domain_to_reversed_parts(self, domain: str) -> tuple[str, ...]:
        return tuple(domain.split(".")[::-1])

    def _reversed_parts_to_domain(self, parts: tuple[str, ...]) -> str:
        return ".".join(parts[::-1])

    def add(self, domain: str, domain_type: DomainType):
        parts = self._domain_to_reversed_parts(domain)
        # Check if already covered by parent suffix or self is already a suffix
        for step in self._trie.prefixes(parts):
            if step.value == DomainType.DOMAIN_SUFFIX:
                return
        # A suffix replaces the whole subtree.  Slicing deletes it in one
        # operation instead of removing every descendant individually.
        if domain_type == DomainType.DOMAIN_SUFFIX and self._trie.has_subtrie(parts):
            del self._trie[parts:]
        self._trie[parts] = domain_type
        if domain_type == DomainType.DOMAIN_WILDCARD:
            self._seen_wildcard = True

    def filter_by_wildcard(self):
        if not self._seen_wildcard:
            return
        wildcards_without_suffix: list[tuple[str, re.Pattern[str]]] = []
        for parts, domain_type in list(self._trie.iteritems()):
            if domain_type != DomainType.DOMAIN_WILDCARD:
                continue
            pattern = self._reversed_parts_to_domain(parts)
            regex = re.compile(wildcard_to_regex(pattern), re.IGNORECASE)
            wildcard_index = next(
                (
                    index
                    for index, label in enumerate(parts)
                    if any(character in label for character in "*?[")
                ),
                len(parts),
            )
            prefix = parts[:wildcard_index]
            if not prefix:
                wildcards_without_suffix.append((pattern, regex))
                continue

            for candidate_parts, candidate_type in list(
                self._trie.iteritems(prefix=prefix)
            ):
                if candidate_type not in (
                    DomainType.DOMAIN,
                    DomainType.DOMAIN_SUFFIX,
                ):
                    continue
                if (
                    candidate_type == DomainType.DOMAIN_SUFFIX
                    and not pattern.startswith("*")
                ):
                    continue
                domain = self._reversed_parts_to_domain(candidate_parts)
                if not regex.fullmatch(domain):
                    continue
                del self._trie[candidate_parts]
                logger.error(f"{candidate_type},{domain} -> DOMAIN-WILDCARD,{pattern}")

        if wildcards_without_suffix:
            for parts, domain_type in list(self._trie.iteritems()):
                if domain_type not in (DomainType.DOMAIN, DomainType.DOMAIN_SUFFIX):
                    continue
                domain = self._reversed_parts_to_domain(parts)
                for pattern, regex in wildcards_without_suffix:
                    if (
                        domain_type == DomainType.DOMAIN_SUFFIX
                        and not pattern.startswith("*")
                    ):
                        continue
                    if not regex.fullmatch(domain):
                        continue
                    _ = self._trie.pop(parts, None)
                    logger.error(f"{domain_type},{domain} -> DOMAIN-WILDCARD,{pattern}")
                    break

    def remove(self, domain: str):
        parts = self._domain_to_reversed_parts(domain)
        _ = self._trie.pop(parts, None)

    def filter_by_domain(self, domain: str):
        try:
            del self._trie[self._domain_to_reversed_parts(domain) :]
        except KeyError:
            pass

    def merge(self, other: Self):
        for d, dt in other.iteritems():
            self.add(d, dt)

    def iteritems(self) -> Iterator[tuple[str, DomainType]]:
        for d, dt in self._trie.iteritems():
            d = self._reversed_parts_to_domain(d)
            yield d, dt

    def items(self) -> list[tuple[str, DomainType]]:
        return list(self.iteritems())

    def sorted_iteritems(self) -> Iterator[tuple[str, DomainType]]:
        self.enable_sorting(True)
        yield from self.iteritems()
        self.enable_sorting(False)

    @override
    def __repr__(self) -> str:
        return ", ".join(f"<'{d}' - {dt}>" for d, dt in self.iteritems())

    def __len__(self) -> int:
        return len(self._trie)

    def enable_sorting(self, enable: bool = True):
        self._trie.enable_sorting(enable)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: type[Self],
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        def validate_from_dict(value: dict[DomainType, list[str]]) -> Self:
            """Validate from dict"""
            trie = cls()
            for domain_type, domains in value.items():
                for domain in domains:
                    trie.add(domain, domain_type)
            return trie

        def serialize_to_dict(instance: Self) -> dict[DomainType, list[str]]:
            """Serialize to dict"""
            data: dict[DomainType, list[str]] = {
                domain_type: [] for domain_type in DomainType
            }
            for domain, domain_type in instance.iteritems():
                data[domain_type].append(domain)
            return data

        dict_schema = core_schema.dict_schema(
            keys_schema=core_schema.enum_schema(
                DomainType, list(DomainType.__members__.values())
            ),
            values_schema=core_schema.list_schema(core_schema.str_schema()),
        )
        chain_schema = core_schema.chain_schema(
            [
                dict_schema,
                core_schema.no_info_plain_validator_function(validate_from_dict),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=chain_schema,
            python_schema=chain_schema,
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize_to_dict,
                return_schema=dict_schema,
            ),
        )


class _BaseIPTrie:
    maxbits: ClassVar[int]

    def __init__(self):
        self._trie = PyTricia(self.maxbits)

    def add(self, ip: str | ipaddress.IPv4Network | ipaddress.IPv6Network):
        if self._trie.get_key(ip):
            return
        self._trie[ip] = None
        for prefix in self._trie.children(ip):
            del self._trie[prefix]

    def iteritems(self) -> Iterator[str]:
        yield from self._trie

    def merge(self, other: Self):
        for ip in other.iteritems():
            self.add(ip)

    @override
    def __repr__(self) -> str:
        return ", ".join(ip for ip in self.iteritems())

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: type[Self],
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        def validate_from_list(value: list[str]) -> Self:
            """Validate from list"""
            trie = cls()
            for ip in value:
                trie.add(ip)
            return trie

        def serialize_to_list(instance: Self) -> list[str]:
            """Serialize to list"""
            return list(instance.iteritems())

        list_schema = core_schema.list_schema(core_schema.str_schema())
        chain_schema = core_schema.chain_schema(
            [
                list_schema,
                core_schema.no_info_plain_validator_function(validate_from_list),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=chain_schema,
            python_schema=chain_schema,
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize_to_list,
                return_schema=list_schema,
            ),
        )


class IPTrie(_BaseIPTrie):
    maxbits: ClassVar[int] = 32


class IPTrie6(_BaseIPTrie):
    maxbits: ClassVar[int] = 128
