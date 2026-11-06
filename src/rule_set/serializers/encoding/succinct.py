from rule_set.errors import SerializerError


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


def build_succinct_set(keys: list[bytes]) -> tuple[list[int], list[int], bytes]:
    """Build the succinct set layout shared by sing-box and mihomo."""
    if not keys:
        raise SerializerError("succinct set requires at least one key")

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
