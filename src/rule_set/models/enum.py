from enum import StrEnum


class SerializeFormat(StrEnum):
    Surge = "surge"
    Loon = "loon"
    Egern = "egern"
    Clash = "clash"
    Sing_Box = "sing-box"
    GeoIP = "geoip"


class DomainType(StrEnum):
    DOMAIN = "DOMAIN"
    DOMAIN_SUFFIX = "DOMAIN_SUFFIX"
    DOMAIN_WILDCARD = "DOMAIN_WILDCARD"
    DOMAIN_REGEX = "DOMAIN_REGEX"
