from collections.abc import Sequence

from rule_set.errors import SerializerError

from .binary import ByteWriter

_PREFIX_LABEL = "\r"
_ROOT_LABEL = "\n"


class _BitSet:
    def __init__(self) -> None:
        self._words: list[int] = []
        self._length: int = 0

    def set(self, index: int) -> None:
        word_index, bit_index = divmod(index, 64)
        while len(self._words) <= word_index:
            self._words.append(0)
        self._words[word_index] |= 1 << bit_index

    def append(self, value: bool) -> None:
        if value:
            self.set(self._length)
        self._length += 1

    @property
    def words(self) -> list[int]:
        return self._words


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
    *, domains: Sequence[str], suffixes: Sequence[str], legacy: bool
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


def _build_succinct_set(keys: Sequence[bytes]) -> tuple[list[int], list[int], bytes]:
    if not keys:
        raise SerializerError("domain matcher requires at least one key")

    leaves = _BitSet()
    label_bitmap = _BitSet()
    labels = bytearray()
    queue: list[tuple[int, int, int]] = [(0, len(keys), 0)]
    queue_index = 0

    while queue_index < len(queue):
        start, end, column = queue[queue_index]
        if column == len(keys[start]):
            start += 1
            leaves.set(queue_index)

        position = start
        while position < end:
            first = position
            label = keys[first][column]
            while position < end and keys[position][column] == label:
                position += 1
            queue.append((first, position, column + 1))
            labels.append(label)
            label_bitmap.append(False)
        label_bitmap.append(True)
        queue_index += 1

    return leaves.words, label_bitmap.words, bytes(labels)


def build_domain_matcher(
    *, domains: Sequence[str], suffixes: Sequence[str], legacy: bool
) -> bytes:
    keys = _domain_keys(domains=domains, suffixes=suffixes, legacy=legacy)
    leaves, label_bitmap, labels = _build_succinct_set(keys)

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
