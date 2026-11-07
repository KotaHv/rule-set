from pathlib import Path
from typing import override

import pytest

from rule_set.config import settings
from rule_set.file_writers.base import BaseFileWriter
from rule_set.metadata import MetadataStore


class _TestFileWriter(BaseFileWriter):
    @property
    @override
    def base_path(self) -> str:
        return "test"

    @property
    @override
    def suffix(self) -> str:
        return ".txt"


@pytest.fixture
def writer_factory(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "build_dir", tmp_path)
    monkeypatch.setattr(settings, "metadata_path", tmp_path / "metadata.db")

    with MetadataStore() as metadata_store:

        def make(data: str | bytes) -> _TestFileWriter:
            return _TestFileWriter(
                data=data,
                target_path=Path("sample"),
                timestamp=123.0,
                metadata_store=metadata_store,
            )

        yield make, metadata_store


def test_missing_file_has_changes_and_is_written(writer_factory):
    make_writer, metadata_store = writer_factory
    writer = make_writer("DOMAIN,example.com\n")

    assert not writer.filepath.exists()
    assert writer.has_changes() is True
    assert writer.write() is True
    assert writer.filepath.read_text(encoding="utf-8") == "DOMAIN,example.com\n"
    assert metadata_store.data[0].path == Path("test/sample.txt")


def test_identical_content_is_not_written(writer_factory):
    make_writer, metadata_store = writer_factory
    writer = make_writer("DOMAIN,example.com\n")
    writer.filepath.parent.mkdir(parents=True)
    writer.filepath.write_text("DOMAIN,example.com\n", encoding="utf-8")

    assert writer.has_changes() is False
    assert writer.write() is False
    assert metadata_store.data == []


def test_only_last_updated_line_is_ignored(writer_factory):
    make_writer, metadata_store = writer_factory
    writer = make_writer(
        "# Total: 1 rules\n# Last Updated: 2026-02-02T00:00:00\nDOMAIN,example.com\n"
    )
    writer.filepath.parent.mkdir(parents=True)
    writer.filepath.write_text(
        "# Total: 1 rules\n# Last Updated: 2026-01-01T00:00:00\nDOMAIN,example.com\n",
        encoding="utf-8",
    )

    assert writer.has_changes() is False
    assert writer.write() is False
    assert metadata_store.data == []


def test_changed_line_is_written(writer_factory):
    make_writer, metadata_store = writer_factory
    writer = make_writer("DOMAIN,new.example.com\n")
    writer.filepath.parent.mkdir(parents=True)
    writer.filepath.write_text("DOMAIN,old.example.com\n", encoding="utf-8")

    assert writer.has_changes() is True
    assert writer.write() is True
    assert writer.filepath.read_text(encoding="utf-8") == "DOMAIN,new.example.com\n"
    assert metadata_store.data[0].path == Path("test/sample.txt")


def test_changed_line_count_is_written(writer_factory):
    make_writer, _ = writer_factory
    writer = make_writer("DOMAIN,example.com\n")
    writer.filepath.parent.mkdir(parents=True)
    writer.filepath.write_text(
        "DOMAIN,example.com\nDOMAIN,extra.example.com\n",
        encoding="utf-8",
    )

    assert writer.has_changes() is True
    assert writer.write() is True
    assert writer.filepath.read_text(encoding="utf-8") == "DOMAIN,example.com\n"


def test_changed_bytes_are_written(writer_factory):
    make_writer, metadata_store = writer_factory
    writer = make_writer(b"\x00\x01")
    writer.filepath.parent.mkdir(parents=True)
    writer.filepath.write_bytes(b"\x00\x02")

    assert writer.has_changes() is True
    assert writer.write() is True
    assert writer.filepath.read_bytes() == b"\x00\x01"
    assert metadata_store.data[0].path == Path("test/sample.txt")


def test_empty_data_is_not_written(writer_factory):
    make_writer, metadata_store = writer_factory
    writer = make_writer("")

    assert writer.write() is False
    assert not writer.filepath.exists()
    assert metadata_store.data == []
