from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CIDR(_message.Message):
    __slots__ = ("ip", "prefix")
    IP_FIELD_NUMBER: _ClassVar[int]
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    ip: bytes
    prefix: int
    def __init__(self, ip: _Optional[bytes] = ..., prefix: _Optional[int] = ...) -> None: ...

class GeoIP(_message.Message):
    __slots__ = ("country_code", "cidr", "inverse_match")
    COUNTRY_CODE_FIELD_NUMBER: _ClassVar[int]
    CIDR_FIELD_NUMBER: _ClassVar[int]
    INVERSE_MATCH_FIELD_NUMBER: _ClassVar[int]
    country_code: str
    cidr: _containers.RepeatedCompositeFieldContainer[CIDR]
    inverse_match: bool
    def __init__(self, country_code: _Optional[str] = ..., cidr: _Optional[_Iterable[_Union[CIDR, _Mapping]]] = ..., inverse_match: _Optional[bool] = ...) -> None: ...

class GeoIPList(_message.Message):
    __slots__ = ("entry",)
    ENTRY_FIELD_NUMBER: _ClassVar[int]
    entry: _containers.RepeatedCompositeFieldContainer[GeoIP]
    def __init__(self, entry: _Optional[_Iterable[_Union[GeoIP, _Mapping]]] = ...) -> None: ...
