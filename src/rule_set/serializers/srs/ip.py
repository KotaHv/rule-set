import ipaddress
from dataclasses import dataclass

from rule_set.errors import SerializerError

from ..encoding.binary import ByteWriter


@dataclass(frozen=True, slots=True)
class _IPRange:
    start: int
    end: int


def _merge_ranges(ranges: list[_IPRange]) -> list[_IPRange]:
    ordered = sorted(ranges, key=lambda item: (item.start, item.end))
    merged: list[_IPRange] = []

    for current in ordered:
        if not merged:
            merged.append(current)
            continue
        previous = merged[-1]
        if current.start <= previous.end + 1:
            if current.end > previous.end:
                merged[-1] = _IPRange(previous.start, current.end)
        else:
            merged.append(current)

    return merged


def _prefix_range(value: str) -> tuple[int, _IPRange]:
    try:
        network = ipaddress.ip_network(value, strict=False)
    except ValueError as exc:
        raise SerializerError(f"invalid ip_cidr: {value!r}") from exc
    return (
        network.version,
        _IPRange(int(network.network_address), int(network.broadcast_address)),
    )


def build_ip_set(values: list[str]) -> bytes:
    ranges4: list[_IPRange] = []
    ranges6: list[_IPRange] = []

    for value in values:
        version, item = _prefix_range(value)
        if version == 4:
            ranges4.append(item)
        else:
            ranges6.append(item)

    ranges4 = _merge_ranges(ranges4)
    ranges6 = _merge_ranges(ranges6)

    writer = ByteWriter()
    writer.write_byte(1)
    writer.write_uint64_be(len(ranges4) + len(ranges6))

    for item in ranges4:
        writer.write_uvarint(4)
        writer.write_uint32_be(item.start)
        writer.write_uvarint(4)
        writer.write_uint32_be(item.end)
    for item in ranges6:
        writer.write_uvarint(16)
        writer.write_bytes(item.start.to_bytes(16, "big"))
        writer.write_uvarint(16)
        writer.write_bytes(item.end.to_bytes(16, "big"))

    return writer.to_bytes()
