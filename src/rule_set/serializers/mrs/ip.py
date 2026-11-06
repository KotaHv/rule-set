import ipaddress
from dataclasses import dataclass

from rule_set.errors import SerializerError

from ..encoding.binary import ByteWriter


@dataclass(frozen=True, slots=True)
class _IPRange:
    version: int
    start: int
    end: int


def _prefix_range(value: str) -> _IPRange:
    try:
        network = ipaddress.ip_network(value, strict=False)
    except ValueError as exc:
        raise SerializerError(f"invalid ip_cidr: {value!r}") from exc
    return _IPRange(
        version=network.version,
        start=int(network.network_address),
        end=int(network.broadcast_address),
    )


def _merge_ranges(ranges: list[_IPRange]) -> list[_IPRange]:
    ordered = sorted(ranges, key=lambda item: (item.version, item.start, item.end))
    merged: list[_IPRange] = []

    for current in ordered:
        if not merged:
            merged.append(current)
            continue
        previous = merged[-1]
        if current.version == previous.version and current.start <= previous.end + 1:
            if current.end > previous.end:
                merged[-1] = _IPRange(previous.version, previous.start, current.end)
        else:
            merged.append(current)

    return merged


def _addr16(version: int, value: int) -> bytes:
    if version == 4:
        return b"\x00" * 10 + b"\xff\xff" + value.to_bytes(4, "big")
    if version == 6:
        return value.to_bytes(16, "big")
    raise SerializerError(f"unsupported IP version: {version}")


def encode_ip_set(payload: list[str]) -> bytes:
    ranges = _merge_ranges([_prefix_range(value) for value in payload])

    writer = ByteWriter()
    writer.write_byte(1)
    writer.write_int64_be(len(ranges))
    for item in ranges:
        writer.write_bytes(_addr16(item.version, item.start))
        writer.write_bytes(_addr16(item.version, item.end))
    return writer.to_bytes()
