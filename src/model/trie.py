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

    def remove(self, domain: str):
        domain = self._reversed_domain(domain)
        self._trie.pop(domain, None)

    def filter_by_domain(self, domain: str):
        try:
            domain = self._reversed_domain(domain)
            for d in self._trie.keys(prefix=domain):
                del self._trie[d]
        except KeyError:
            pass

    def merge(self, other: Self):
        for d, dt in other.iteritems():
            self.add(d, dt)

    def iteritems(self) -> Iterator[tuple[str, DomainType]]:
        for d, dt in self._trie.iteritems():
            d = self._reversed_domain(d)
            yield d, dt

    def items(self) -> list[tuple[str, DomainType]]:
        return list(self.iteritems())

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
        def validate_from_dict(value: dict[DomainType, list[str]]) -> Self:
            """Validate from dict"""
            trie = cls()
            for domain_type, domains in value.items():
                for domain in domains:
                    trie.add(domain, domain_type)
            return trie

        def serialize_to_dict(instance: Self) -> dict[DomainType, list[str]]:
            """Serialize to dict"""
            data = {domain_type: [] for domain_type in DomainType}
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
