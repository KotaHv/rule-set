from ...models import SerializeFormat
from .base import BaseSerializer
from .clash import ClashSerializer
from .egern import EgernSerializer
from .loon import LoonSerializer
from .sing_box import SingBoxSerializer
from .surge import SurgeSerializer
from .v2ray_geo_ip import GeoIPSerializer

client_serializers: dict[SerializeFormat, type[BaseSerializer]] = {
    SerializeFormat.Surge: SurgeSerializer,
    SerializeFormat.Loon: LoonSerializer,
    SerializeFormat.Clash: ClashSerializer,
    SerializeFormat.Egern: EgernSerializer,
    SerializeFormat.Sing_Box: SingBoxSerializer,
    SerializeFormat.GeoIP: GeoIPSerializer,
}

__all__ = [
    SurgeSerializer,
    LoonSerializer,
    ClashSerializer,
    EgernSerializer,
    SingBoxSerializer,
    GeoIPSerializer,
    client_serializers,
]
