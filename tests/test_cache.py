import os
import time
from pathlib import Path

from rule_set.cache import Cache


def test_cache_round_trips_text_and_bytes(tmp_path: Path) -> None:
    cache = Cache(path=tmp_path)

    assert cache.store("text", "value") is not None
    assert cache.store("binary", b"\x00\xff") is not None

    assert cache.retrieve_text("text") == "value"
    assert cache.retrieve_bytes("text") == b"value"
    assert cache.retrieve_bytes("binary") == b"\x00\xff"


def test_cache_retrieves_empty_text(tmp_path: Path) -> None:
    cache = Cache(path=tmp_path)

    assert cache.store("empty", "") is not None
    assert cache.retrieve_text("empty") == ""


def test_cache_store_replaces_existing_value(tmp_path: Path) -> None:
    cache = Cache(path=tmp_path)

    assert cache.store("key", "first") is not None
    assert cache.store("key", "second") is not None

    assert cache.retrieve_text("key") == "second"
    assert not any(path.suffix == ".tmp" for path in cache.cache_directory.iterdir())


def test_cache_expires_retrieved_path(tmp_path: Path) -> None:
    cache = Cache(path=tmp_path, ttl_hours=1)
    filepath = cache.store("key", "value")
    assert filepath is not None
    assert cache.retrieve_path("key") == filepath

    old = time.time() - 2 * 60 * 60
    os.utime(filepath, (old, old))

    assert cache.retrieve_path("key") is None
    assert not filepath.exists()
