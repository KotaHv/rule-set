from rule_set.errors import SerializerError


class ByteWriter:
    def __init__(self) -> None:
        self._data: bytearray = bytearray()

    def write_byte(self, value: int) -> None:
        if not 0 <= value <= 0xFF:
            raise SerializerError(f"byte out of range: {value}")
        self._data.append(value)

    def write_bytes(self, value: bytes) -> None:
        self._data.extend(value)

    def write_uvarint(self, value: int) -> None:
        if value < 0:
            raise SerializerError(f"uvarint cannot be negative: {value}")
        while value >= 0x80:
            self._data.append((value & 0x7F) | 0x80)
            value >>= 7
        self._data.append(value)

    def write_uint16_be(self, value: int) -> None:
        if not 0 <= value <= 0xFFFF:
            raise SerializerError(f"uint16 out of range: {value}")
        self._data.extend(value.to_bytes(2, "big"))

    def write_uint32_be(self, value: int) -> None:
        if not 0 <= value <= 0xFFFFFFFF:
            raise SerializerError(f"uint32 out of range: {value}")
        self._data.extend(value.to_bytes(4, "big"))

    def write_int64_be(self, value: int) -> None:
        if not -(1 << 63) <= value < (1 << 63):
            raise SerializerError(f"int64 out of range: {value}")
        self._data.extend(value.to_bytes(8, "big", signed=True))

    def write_uint64_be(self, value: int) -> None:
        if not 0 <= value <= 0xFFFFFFFFFFFFFFFF:
            raise SerializerError(f"uint64 out of range: {value}")
        self._data.extend(value.to_bytes(8, "big"))

    def to_bytes(self) -> bytes:
        return bytes(self._data)
