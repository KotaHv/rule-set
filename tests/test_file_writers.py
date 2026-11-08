from pathlib import Path

import pytest

from rule_set.file_writers import write_if_changed


@pytest.fixture
def filepath(tmp_path: Path) -> Path:
    return tmp_path / "test" / "sample.txt"


def test_missing_file_is_written(filepath: Path) -> None:
    assert not filepath.exists()
    assert write_if_changed(filepath, "DOMAIN,example.com\n") is True
    assert filepath.read_text(encoding="utf-8") == "DOMAIN,example.com\n"


def test_identical_content_is_not_written(filepath: Path) -> None:
    filepath.parent.mkdir(parents=True)
    _ = filepath.write_text("DOMAIN,example.com\n", encoding="utf-8")

    assert write_if_changed(filepath, "DOMAIN,example.com\n") is False


def test_only_last_updated_line_is_ignored(filepath: Path) -> None:
    filepath.parent.mkdir(parents=True)
    _ = filepath.write_text(
        "# Total: 1 rules\n# Last Updated: 2026-01-01T00:00:00\nDOMAIN,example.com\n",
        encoding="utf-8",
    )

    assert (
        write_if_changed(
            filepath,
            "# Total: 1 rules\n# Last Updated: 2026-02-02T00:00:00\nDOMAIN,example.com\n",
        )
        is False
    )


def test_changed_line_is_written(filepath: Path) -> None:
    filepath.parent.mkdir(parents=True)
    _ = filepath.write_text("DOMAIN,old.example.com\n", encoding="utf-8")

    assert write_if_changed(filepath, "DOMAIN,new.example.com\n") is True
    assert filepath.read_text(encoding="utf-8") == "DOMAIN,new.example.com\n"


def test_changed_line_count_is_written(filepath: Path) -> None:
    filepath.parent.mkdir(parents=True)
    _ = filepath.write_text(
        "DOMAIN,example.com\nDOMAIN,extra.example.com\n",
        encoding="utf-8",
    )

    assert write_if_changed(filepath, "DOMAIN,example.com\n") is True
    assert filepath.read_text(encoding="utf-8") == "DOMAIN,example.com\n"


def test_changed_bytes_are_written(filepath: Path) -> None:
    filepath.parent.mkdir(parents=True)
    _ = filepath.write_bytes(b"\x00\x02")

    assert write_if_changed(filepath, b"\x00\x01") is True
    assert filepath.read_bytes() == b"\x00\x01"


def test_empty_data_is_not_written(filepath: Path) -> None:
    assert write_if_changed(filepath, "") is False
    assert not filepath.exists()
