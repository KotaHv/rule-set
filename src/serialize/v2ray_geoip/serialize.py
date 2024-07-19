import ipaddress

from . import geoip_pb2
from model import RuleModel, SerializeOption


class Serialize:
    def __init__(self, *, rules: RuleModel, option: SerializeOption) -> None:
        self.rules = rules
        self.option = option

    def serialize(self) -> bytes | None:
        if not self.rules.is_only_ip_cidr_rules():
            return
        ip_list = []
        ip_list.extend(self.rules.ip_cidr)
        ip_list.extend(self.rules.ip_cidr6)
        geoip = geoip_pb2.GeoIP()
        geoip.country_code = self.option.geoip_country_code
        geoip.inverse_match = False
        for ip in ip_list:
            cidr = geoip_pb2.CIDR()
            ip = ipaddress.ip_network(ip)
            cidr.ip = ip.network_address.packed
            cidr.prefix = ip.prefixlen
            geoip.cidr.append(cidr)

        geoip_list = geoip_pb2.GeoIPList()
        geoip_list.entry.append(geoip)
        serialized_data = geoip_list.SerializeToString()
        return serialized_data
