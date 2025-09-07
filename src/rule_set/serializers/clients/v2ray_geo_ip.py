import ipaddress

from ..v2ray_geo_ip import geo_ip_pb2
from .base import BaseSerializer


class GeoIPSerializer(BaseSerializer):
    def serialize(self) -> bytes | None:
        ip_list = []
        ip_list.extend(self.rules.ip_cidr)
        ip_list.extend(self.rules.ip_cidr6)
        geo_ip = geo_ip_pb2.GeoIP()
        geo_ip.country_code = self.option.geo_ip.country_code
        geo_ip.inverse_match = False
        for ip in ip_list:
            cidr = geo_ip_pb2.CIDR()
            ip = ipaddress.ip_network(ip)
            cidr.ip = ip.network_address.packed
            cidr.prefix = ip.prefixlen
            geo_ip.cidr.append(cidr)

        geo_ip_list = geo_ip_pb2.GeoIPList()
        geo_ip_list.entry.append(geo_ip)
        serialized_data = geo_ip_list.SerializeToString()
        return serialized_data
