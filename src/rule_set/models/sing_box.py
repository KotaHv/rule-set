from typing import Literal, NotRequired, TypedDict


class SingBoxLeafRule(TypedDict, total=False):
    query_type: str
    network: str
    domain: str
    domain_suffix: str
    domain_keyword: str
    domain_regex: str
    source_ip_cidr: str
    ip_cidr: str
    source_port: int
    source_port_range: str
    port: int
    port_range: str
    process_name: str
    process_path: str
    package_name: str
    wifi_ssid: str
    wifi_bssid: str
    invert: bool


class SingBoxLogicalRule(TypedDict):
    type: Literal["logical"]
    rules: list[SingBoxLeafRule | SingBoxLogicalRule]
    mode: Literal["and", "or"]
    invert: NotRequired[bool]


class SingBoxClientRule(TypedDict, total=False):
    domain: list[str]
    domain_suffix: list[str]
    domain_regex: list[str]
    domain_keyword: list[str]
    ip_cidr: list[str]
    process_name: list[str]


type SingBoxRule = SingBoxLeafRule | SingBoxLogicalRule


class SingBoxRuleSet(TypedDict):
    version: Literal[2]
    rules: list[SingBoxClientRule | SingBoxRule]
