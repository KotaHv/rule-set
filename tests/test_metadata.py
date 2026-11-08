from pathlib import Path

import pytest

from rule_set.config import settings
from rule_set.metadata import MetadataStore
from rule_set.models import MetadataRecord


@pytest.fixture
def metadata_store(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "metadata_path", tmp_path / "metadata.db")
    with MetadataStore() as store:
        yield store


def test_update_stores_build_relative_path(metadata_store):
    record = MetadataRecord(path=Path("sing-box/sample.json"), timestamp=123.0)

    metadata_store.update(record)

    assert metadata_store.data == [record]


def test_update_rejects_absolute_path(metadata_store, tmp_path):
    record = MetadataRecord(path=tmp_path / "sample.json", timestamp=123.0)

    with pytest.raises(ValueError, match="relative"):
        metadata_store.update(record)

    assert metadata_store.data == []
