from typing import Any, Iterator, Self
from pygtrie import StringTrie
from pydantic_core import core_schema
from pydantic import GetCoreSchemaHandler

from .enum import DomainType


class DomainTrie:
    def __init__(self):
        self._trie = StringTrie(separator=".")

    def _reversed_domain(self, domain: str) -> str:
        return ".".join(reversed(domain.split(".")))

    def add(self, domain: str, domain_type: DomainType):
        domain = self._reversed_domain(domain)
        # Check if already covered by parent suffix or self is already a suffix
        for _, dt in self._trie.prefixes(domain):
            if dt == DomainType.DOMAIN_SUFFIX:
                return
        self._trie[domain] = domain_type
        if domain_type != DomainType.DOMAIN_SUFFIX:
            return
        # Clear children if suffix
        for d in self._trie.keys(prefix=domain):
            if d == domain:
                continue
            del self._trie[d]

    def merge(self, other: Self):
        for d, dt in other.iteritems():
            self.add(d, dt)

    def iteritems(self) -> Iterator[tuple[str, DomainType]]:
        for d, dt in self._trie.iteritems():
            d = self._reversed_domain(d)
            yield d, dt

    def sorted_iteritems(self) -> Iterator[tuple[str, DomainType]]:
        self.enable_sorting(True)
        yield from self.iteritems()
        self.enable_sorting(False)

    def __repr__(self) -> str:
        return ", ".join(f"<'{d}' - {dt}>" for d, dt in self.iteritems())

    def enable_sorting(self, enable: bool = True):
        self._trie.enable_sorting(enable)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        def validate_from_list(value: list[tuple[str, DomainType]]) -> Self:
            """Validate from list of tuples"""
            trie = cls()
            for domain, domain_type in value:
                trie.add(domain, domain_type)
            return trie

        def serialize_to_list(instance: Self) -> list[tuple[str, DomainType]]:
            """Serialize to list of tuples"""
            return [
                (domain, domain_type) for domain, domain_type in instance.iteritems()
            ]

        list_schema = core_schema.list_schema(
            items_schema=core_schema.tuple_schema(
                [
                    core_schema.str_schema(),
                    core_schema.enum_schema(
                        DomainType, list(DomainType.__members__.values())
                    ),
                ],
            )
        )
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
