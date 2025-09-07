from .clash import FileWriter as ClashFileWriter
from .egern import FileWriter as EgernFileWriter
from .geoip import FileWriter as GeoIPFileWriter
from .loon import FileWriter as LoonFileWriter
from .sing_box import FileWriter as SingBoxFileWriter
from .surge import FileWriter as SurgeFileWriter

__all__ = [
    SurgeFileWriter,
    LoonFileWriter,
    ClashFileWriter,
    EgernFileWriter,
    SingBoxFileWriter,
    GeoIPFileWriter,
]
