from rule_set.errors import SerializerError

from ..encoding.binary import ByteWriter
from ..encoding.succinct import build_succinct_set

_PREFIX_LABEL = "\r"
_ROOT_LABEL = "\n"


def _reverse_domain(value: str) -> str:
    # Go reverses runes, not UTF-8 bytes. Python string slicing reverses code
    # points, which is equivalent for valid Unicode domains.
    return value[::-1]


def _encode_domain(value: str, *, prefix: str = "") -> bytes:
    try:
        return (_reverse_domain(prefix + value)).encode("utf-8")
    except UnicodeEncodeError as exc:
        raise SerializerError(f"invalid domain: {value!r}") from exc


def _domain_keys(
    *, domains: list[str], suffixes: list[str], legacy: bool
) -> list[bytes]:
    keys: list[bytes] = []
    seen: set[str] = set()

    for suffix in suffixes:
        if not suffix:
            raise SerializerError("domain_suffix: empty item is not allowed")
        if suffix in seen:
            continue
        seen.add(suffix)
        if suffix.startswith("."):
            keys.append(_encode_domain(suffix, prefix=_PREFIX_LABEL))
        elif legacy:
            keys.append(_encode_domain(suffix))
            suffix_domain = "." + suffix
            if suffix_domain not in seen:
                seen.add(suffix_domain)
                keys.append(_encode_domain(suffix_domain, prefix=_PREFIX_LABEL))
        else:
            keys.append(_encode_domain(suffix, prefix=_ROOT_LABEL))

    for domain in domains:
        if not domain:
            raise SerializerError("domain: empty item is not allowed")
        if domain in seen:
            continue
        seen.add(domain)
        keys.append(_encode_domain(domain))

    # Go sorts strings by their UTF-8 bytes, then compacts adjacent duplicates.
    return sorted(set(keys))


def build_domain_matcher(
    *, domains: list[str], suffixes: list[str], legacy: bool
) -> bytes:
    keys = _domain_keys(domains=domains, suffixes=suffixes, legacy=legacy)
    leaves, label_bitmap, labels = build_succinct_set(keys)

    writer = ByteWriter()
    writer.write_byte(0)
    writer.write_uvarint(len(leaves))
    for word in leaves:
        writer.write_uint64_be(word)
    writer.write_uvarint(len(label_bitmap))
    for word in label_bitmap:
        writer.write_uint64_be(word)
    writer.write_uvarint(len(labels))
    writer.write_bytes(labels)
    return writer.to_bytes()
