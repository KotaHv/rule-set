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
    DOMAIN_SUFFIX = "DOMAIN-SUFFIX"
    DOMAIN_WILDCARD = "DOMAIN-WILDCARD"


class ProcessingRuleType(StrEnum):
    DOMAIN = "DOMAIN"
    DOMAIN_SUFFIX = "DOMAIN-SUFFIX"
    DOMAIN_WILDCARD = "DOMAIN-WILDCARD"
    DOMAIN_REGEX = "DOMAIN-REGEX"
    DOMAIN_KEYWORD = "DOMAIN-KEYWORD"
    IP_CIDR = "IP-CIDR"
    IP_CIDR6 = "IP-CIDR6"
    IP_ASN = "IP-ASN"
    LOGICAL = "LOGICAL"
    PROCESS_NAME = "PROCESS-NAME"
    USER_AGENT = "USER-AGENT"
    URL_REGEX = "URL-REGEX"
