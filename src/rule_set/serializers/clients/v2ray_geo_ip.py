import ipaddress
from typing import override

from rule_set.errors import SerializerError
from rule_set.models import Artifact, ArtifactKind

from ..v2ray_geo_ip import geo_ip_pb2
from .base import BaseSerializer


class GeoIPSerializer(BaseSerializer):
    @override
    def serialize(self) -> list[Artifact]:
        country_code = self.option.geo_ip.country_code
        if country_code is None:
            raise SerializerError("GeoIP serialization requires a country code")

        ip_list: list[str] = []
        ip_list.extend(self.rules.ip_cidr)
        ip_list.extend(self.rules.ip_cidr6)
        geo_ip = geo_ip_pb2.GeoIP()
        geo_ip.country_code = country_code
        geo_ip.inverse_match = False
        for ip in ip_list:
            cidr = geo_ip_pb2.CIDR()
            network = ipaddress.ip_network(ip)
            cidr.ip = network.network_address.packed
            cidr.prefix = network.prefixlen
            geo_ip.cidr.append(cidr)

        geo_ip_list = geo_ip_pb2.GeoIPList()
        geo_ip_list.entry.append(geo_ip)
        serialized_data = geo_ip_list.SerializeToString()
        return [Artifact(kind=ArtifactKind.DEFAULT, data=serialized_data)]
