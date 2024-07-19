from .surge import FileWriter as SurgeFileWriter
from .loon import FileWriter as LoonFileWriter
from .clash import FileWriter as ClashFileWriter
from .egern import FileWriter as EgernFileWriter
from .sing_box import FileWriter as SingBoxFileWriter

__all__ = [
    SurgeFileWriter,
    LoonFileWriter,
    ClashFileWriter,
    EgernFileWriter,
    SingBoxFileWriter,
]
