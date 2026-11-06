from collections.abc import Callable, Sequence
from enum import IntEnum
from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from rule_set.errors import SerializerError

from .binary import ByteWriter
from .domain import build_domain_matcher
from .ip import build_ip_set

_BOOL_NOT_UINT16 = "boolean is not a valid uint16"


def _reject_bool_uint16(value: int) -> int:
    if isinstance(value, bool):
        raise ValueError(_BOOL_NOT_UINT16)
    return value


_UInt16 = Annotated[int, BeforeValidator(_reject_bool_uint16), Field(ge=0, le=0xFFFF)]
_InterfaceType = Literal["wifi", "cellular", "ethernet", "other"]


def _listify_str(value: str | list[str]) -> list[str]:
    if isinstance(value, str):
        return [value]
    return value


def _listify_uint16(value: int | list[int]) -> list[int]:
    if isinstance(value, bool):
        raise ValueError(_BOOL_NOT_UINT16)
    if isinstance(value, int):
        return [value]
    return value


_ListableStr = Annotated[list[str], BeforeValidator(_listify_str)]
_ListableUInt16 = Annotated[list[_UInt16], BeforeValidator(_listify_uint16)]
_ListableInterfaceType = Annotated[list[_InterfaceType], BeforeValidator(_listify_str)]

_INTERFACE_TYPES: dict[_InterfaceType, int] = {
    "wifi": 0,
    "cellular": 1,
    "ethernet": 2,
    "other": 3,
}


class _RuleItem(IntEnum):
    QUERY_TYPE = 0
    NETWORK = 1
    DOMAIN = 2
    DOMAIN_KEYWORD = 3
    DOMAIN_REGEX = 4
    SOURCE_IP_CIDR = 5
    IP_CIDR = 6
    SOURCE_PORT = 7
    SOURCE_PORT_RANGE = 8
    PORT = 9
    PORT_RANGE = 10
    PROCESS_NAME = 11
    PROCESS_PATH = 12
    PACKAGE_NAME = 13
    WIFI_SSID = 14
    WIFI_BSSID = 15
    ADGUARD_DOMAIN = 16
    PROCESS_PATH_REGEX = 17
    NETWORK_TYPE = 18
    NETWORK_IS_EXPENSIVE = 19
    NETWORK_IS_CONSTRAINED = 20
    NETWORK_INTERFACE_ADDRESS = 21
    DEFAULT_INTERFACE_ADDRESS = 22
    PACKAGE_NAME_REGEX = 23
    FINAL = 0xFF


class DefaultRuleSource(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    type: Literal["", "default"] = "default"
    query_type: _ListableUInt16 = []
    network: _ListableStr = []
    domain: _ListableStr = []
    domain_suffix: _ListableStr = []
    domain_keyword: _ListableStr = []
    domain_regex: _ListableStr = []
    source_ip_cidr: _ListableStr = []
    ip_cidr: _ListableStr = []
    source_port: _ListableUInt16 = []
    source_port_range: _ListableStr = []
    port: _ListableUInt16 = []
    port_range: _ListableStr = []
    process_name: _ListableStr = []
    process_path: _ListableStr = []
    process_path_regex: _ListableStr = []
    package_name: _ListableStr = []
    package_name_regex: _ListableStr = []
    network_type: _ListableInterfaceType = []
    network_is_expensive: bool = False
    network_is_constrained: bool = False
    wifi_ssid: _ListableStr = []
    wifi_bssid: _ListableStr = []
    invert: bool = False


class LogicalRuleSource(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    type: Literal["logical"]
    mode: Literal["and", "or"]
    rules: Annotated[list[DefaultRuleSource | LogicalRuleSource], Field(min_length=1)]
    invert: bool = False


class RuleSetSource(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    version: Annotated[int, Field(ge=1, le=5)]
    rules: list[DefaultRuleSource | LogicalRuleSource] = []


def _write_string_item(
    writer: ByteWriter, item_type: _RuleItem, values: Sequence[str]
) -> None:
    writer.write_byte(item_type)
    writer.write_string_list(list(values))


def _write_optional_string_item(
    writer: ByteWriter, item_type: _RuleItem, values: Sequence[str]
) -> None:
    if values:
        _write_string_item(writer, item_type, values)


def _write_optional_uint16_item(
    writer: ByteWriter, item_type: _RuleItem, values: Sequence[int]
) -> None:
    if values:
        writer.write_byte(item_type)
        writer.write_uint16_list(list(values))


def _interface_type(value: _InterfaceType) -> int:
    return _INTERFACE_TYPES[value]


def _write_default_rule(
    writer: ByteWriter, rule: DefaultRuleSource, version: int
) -> None:
    writer.write_byte(0)

    _write_optional_uint16_item(writer, _RuleItem.QUERY_TYPE, rule.query_type)

    if rule.network:
        _write_string_item(writer, _RuleItem.NETWORK, rule.network)

    if rule.domain or rule.domain_suffix:
        writer.write_byte(_RuleItem.DOMAIN)
        writer.write_bytes(
            build_domain_matcher(
                domains=rule.domain,
                suffixes=rule.domain_suffix,
                legacy=version == 1,
            )
        )

    _write_optional_string_item(writer, _RuleItem.DOMAIN_KEYWORD, rule.domain_keyword)
    _write_optional_string_item(writer, _RuleItem.DOMAIN_REGEX, rule.domain_regex)

    if rule.source_ip_cidr:
        writer.write_byte(_RuleItem.SOURCE_IP_CIDR)
        writer.write_bytes(build_ip_set(rule.source_ip_cidr))

    if rule.ip_cidr:
        writer.write_byte(_RuleItem.IP_CIDR)
        writer.write_bytes(build_ip_set(rule.ip_cidr))

    _write_optional_uint16_item(writer, _RuleItem.SOURCE_PORT, rule.source_port)
    _write_optional_string_item(
        writer, _RuleItem.SOURCE_PORT_RANGE, rule.source_port_range
    )
    _write_optional_uint16_item(writer, _RuleItem.PORT, rule.port)
    _write_optional_string_item(writer, _RuleItem.PORT_RANGE, rule.port_range)
    _write_optional_string_item(writer, _RuleItem.PROCESS_NAME, rule.process_name)
    _write_optional_string_item(writer, _RuleItem.PROCESS_PATH, rule.process_path)
    _write_optional_string_item(
        writer, _RuleItem.PROCESS_PATH_REGEX, rule.process_path_regex
    )
    _write_optional_string_item(writer, _RuleItem.PACKAGE_NAME, rule.package_name)

    if rule.package_name_regex:
        if version < 5:
            raise SerializerError(
                "package_name_regex is only supported in rule-set version 5 or later"
            )
        _write_string_item(
            writer, _RuleItem.PACKAGE_NAME_REGEX, rule.package_name_regex
        )

    if rule.network_type:
        if version < 3:
            raise SerializerError(
                "network_type is only supported in rule-set version 3 or later"
            )
        writer.write_byte(_RuleItem.NETWORK_TYPE)
        writer.write_uint8_list([_interface_type(value) for value in rule.network_type])

    if rule.network_is_expensive:
        if version < 3:
            raise SerializerError(
                "network_is_expensive is only supported in rule-set version 3 or later"
            )
        writer.write_byte(_RuleItem.NETWORK_IS_EXPENSIVE)

    if rule.network_is_constrained:
        if version < 3:
            raise SerializerError(
                "network_is_constrained is only supported in rule-set version 3 or later"
            )
        writer.write_byte(_RuleItem.NETWORK_IS_CONSTRAINED)

    _write_optional_string_item(writer, _RuleItem.WIFI_SSID, rule.wifi_ssid)
    _write_optional_string_item(writer, _RuleItem.WIFI_BSSID, rule.wifi_bssid)

    writer.write_byte(_RuleItem.FINAL)
    writer.write_byte(1 if rule.invert else 0)


def _write_logical_rule(
    writer: ByteWriter, rule: LogicalRuleSource, version: int
) -> None:
    writer.write_byte(1)
    writer.write_byte(0 if rule.mode == "and" else 1)
    writer.write_uvarint(len(rule.rules))
    for child in rule.rules:
        write_rule(writer, child, version)
    writer.write_byte(1 if rule.invert else 0)


def write_rule(
    writer: ByteWriter,
    rule: DefaultRuleSource | LogicalRuleSource,
    version: int,
) -> None:
    if isinstance(rule, LogicalRuleSource):
        _write_logical_rule(writer, rule, version)
    else:
        _write_default_rule(writer, rule, version)


def encode_payload(rule_set: RuleSetSource, version: int) -> bytes:
    writer = ByteWriter()
    writer.write_uvarint(len(rule_set.rules))
    for rule in rule_set.rules:
        write_rule(writer, rule, version)
    return writer.to_bytes()


def _has_default_rule(
    rules: Sequence[DefaultRuleSource | LogicalRuleSource],
    predicate: Callable[[DefaultRuleSource], bool],
) -> bool:
    for rule in rules:
        if isinstance(rule, LogicalRuleSource):
            if _has_default_rule(rule.rules, predicate):
                return True
        elif predicate(rule):
            return True
    return False


def _needs_version_3(rule: DefaultRuleSource) -> bool:
    return (
        bool(rule.network_type)
        or rule.network_is_expensive
        or rule.network_is_constrained
    )


def _needs_version_5(rule: DefaultRuleSource) -> bool:
    return bool(rule.package_name_regex)


def output_version(rule_set: RuleSetSource) -> int:
    version = rule_set.version
    if version == 5 and not _has_default_rule(rule_set.rules, _needs_version_5):
        version = 4
    if version == 4:
        # network_interface_address and default_interface_address are not
        # modeled yet; unsupported input is rejected by pydantic before this.
        version = 3
    if version == 3 and not _has_default_rule(rule_set.rules, _needs_version_3):
        version = 2
    return version
