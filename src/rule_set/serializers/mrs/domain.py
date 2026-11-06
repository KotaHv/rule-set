from rule_set.errors import SerializerError

from ..encoding.binary import ByteWriter
from ..encoding.succinct import build_succinct_set

_DOT_WILDCARD = ""
_COMPLEX_WILDCARD = "+"
_STAR_WILDCARD = "*"


def _lower_domain(value: str) -> str:
    if value.isascii():
        return value.lower()
    # Go's strings.ToLower uses a context-free, single-rune mapping. Python's
    # str.lower() is context-sensitive (final sigma) and can expand one rune
    # into several (U+0130), so lower non-ASCII input rune by rune.
    return "".join(character.lower()[0] for character in value)


def _invalid_domain(value: str, reason: str) -> SerializerError:
    return SerializerError(f"invalid domain: {value!r}: {reason}")


def _split_domain(value: str) -> list[str]:
    if not value:
        raise SerializerError("invalid domain: empty item is not allowed")
    if value.endswith("."):
        raise _invalid_domain(value, "trailing dot is not allowed")
    if value[0].isspace() or value[-1].isspace():
        raise _invalid_domain(value, "leading or trailing whitespace is not allowed")

    parts = _lower_domain(value).split(".")
    if len(parts) == 1:
        if not parts[0]:
            raise SerializerError("invalid domain: empty item is not allowed")
    else:
        for index, part in enumerate(parts[1:], start=2):
            if not part:
                raise _invalid_domain(value, f"label {index} is empty")

    for index, part in enumerate(parts):
        if _COMPLEX_WILDCARD in part:
            if part != _COMPLEX_WILDCARD:
                raise _invalid_domain(value, "'+' must occupy the entire label")
            if index != 0:
                raise _invalid_domain(value, "'+' is only allowed in the first label")
            if len(parts) == 1:
                raise _invalid_domain(value, "'+' must be followed by another label")
        if _STAR_WILDCARD in part and part != _STAR_WILDCARD:
            raise _invalid_domain(value, "'*' must occupy the entire label")

    return parts


def _encode_parts(parts: list[str]) -> bytes:
    if not parts:
        raise SerializerError("invalid domain: empty item is not allowed")

    labels = list(parts)
    if labels[0] == _DOT_WILDCARD:
        labels[0] = _COMPLEX_WILDCARD

    try:
        return ".".join(labels)[::-1].encode("utf-8")
    except UnicodeEncodeError as exc:
        raise SerializerError(f"invalid domain: {parts!r}") from exc


def _domain_keys(value: str) -> list[bytes]:
    if "/" in value:
        raise _invalid_domain(value, "slash is not allowed")

    parts = _split_domain(value)
    if parts[0] == _COMPLEX_WILDCARD:
        return [_encode_parts(parts[1:]), _encode_parts(parts)]
    return [_encode_parts(parts)]


def encode_domain_set(payload: list[str]) -> bytes:
    keys: list[bytes] = []
    for rule in payload:
        keys.extend(_domain_keys(rule))

    leaves, label_bitmap, labels = build_succinct_set(sorted(set(keys)))

    writer = ByteWriter()
    writer.write_byte(1)
    writer.write_int64_be(len(leaves))
    for word in leaves:
        writer.write_uint64_be(word)
    writer.write_int64_be(len(label_bitmap))
    for word in label_bitmap:
        writer.write_uint64_be(word)
    writer.write_int64_be(len(labels))
    writer.write_bytes(labels)
    return writer.to_bytes()
