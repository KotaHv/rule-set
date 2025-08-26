from enum import Enum


class SerializeFormat(str, Enum):
    Surge = "surge"
    Loon = "loon"
    Egern = "egern"
    Clash = "clash"
    Sing_Box = "sing-box"
    GeoIP = "geoip"


class V2rayAttrMode(str, Enum):
    ALL = "ALL"
    NO_ATTR = "NO_ATTR"
    ATTRS = "ATTRS"
    EXCLUDE_ATTRS = "EXCLUDE_ATTRS"
