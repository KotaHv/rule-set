import zlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from rule_set.config import settings
from rule_set.errors import SerializerError
from rule_set.file_writers.sing_box import SingBoxFileWriter
from rule_set.metadata import MetadataStore
from rule_set.serializers.srs import encode_rule_set
from rule_set.serializers.srs.binary import ByteWriter

FIXTURES = Path(__file__).parent / "fixtures" / "srs"


@pytest.mark.parametrize(
    "source_path",
    sorted(FIXTURES.glob("*.json")),
    ids=lambda path: path.stem,
)
def test_srs_matches_sing_box_reference(source_path: Path) -> None:
    reference = source_path.with_suffix(".srs").read_bytes()
    actual = encode_rule_set(source_path.read_bytes())

    assert actual[:3] == b"SRS"
    assert actual[3] == reference[3]
    assert zlib.decompress(actual[4:]) == zlib.decompress(reference[4:])


def test_uvarint_encoding() -> None:
    cases = [
        (0, b"\x00"),
        (127, b"\x7f"),
        (128, b"\x80\x01"),
        (300, b"\xac\x02"),
        (16384, b"\x80\x80\x01"),
    ]

    for value, expected in cases:
        writer = ByteWriter()
        writer.write_uvarint(value)
        assert writer.to_bytes() == expected


def test_downgrades_version_when_features_are_absent() -> None:
    encoded = encode_rule_set('{"version": 5, "rules": [{"domain": ["example.com"]}]}')

    assert encoded[3] == 2


def test_rejects_unknown_rule_fields() -> None:
    with pytest.raises(ValidationError):
        encode_rule_set(
            '{"version": 2, "rules": [{"adguard_domain": ["||ads.example^"]}]}'
        )


def test_rejects_network_type_before_version_3() -> None:
    with pytest.raises(SerializerError, match="version 3"):
        encode_rule_set('{"version": 2, "rules": [{"network_type": ["wifi"]}]}')


def test_rejects_package_name_regex_before_version_5() -> None:
    with pytest.raises(SerializerError, match="version 5"):
        encode_rule_set('{"version": 2, "rules": [{"package_name_regex": ["^com"]}]}')


def test_rejects_unknown_network_type() -> None:
    with pytest.raises(ValidationError):
        encode_rule_set('{"version": 3, "rules": [{"network_type": ["bluetooth"]}]}')


def test_rejects_empty_logical_rule() -> None:
    with pytest.raises(ValidationError):
        encode_rule_set(
            '{"version": 2, "rules": [{"type": "logical", "mode": "and", "rules": []}]}'
        )


def test_rejects_empty_domain_item() -> None:
    with pytest.raises(SerializerError, match="domain_suffix"):
        encode_rule_set('{"version": 2, "rules": [{"domain_suffix": [""]}]}')


def test_rejects_invalid_ip_cidr() -> None:
    with pytest.raises(SerializerError, match="invalid ip_cidr"):
        encode_rule_set('{"version": 2, "rules": [{"ip_cidr": ["not-a-cidr"]}]}')


@pytest.mark.parametrize(
    "payload",
    [
        '{"version": 2, "rules": [{"query_type": true}]}',
        '{"version": 2, "rules": [{"query_type": [true]}]}',
        '{"version": 2, "rules": [{"source_port": false}]}',
        '{"version": 2, "rules": [{"port": [false]}]}',
    ],
)
def test_rejects_boolean_uint16_values(payload: str) -> None:
    with pytest.raises(ValidationError):
        encode_rule_set(payload)


def _fail_subprocess(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("the SRS writer must not invoke an external process")


def test_file_writer_generates_srs_without_sing_box(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "build_dir", tmp_path)
    monkeypatch.setattr(settings, "metadata_path", tmp_path / "metadata.db")
    monkeypatch.setattr("subprocess.run", _fail_subprocess)
    data = (FIXTURES / "logical.json").read_text(encoding="utf-8")
    reference = (FIXTURES / "logical.srs").read_bytes()

    with MetadataStore() as metadata_store:
        writer = SingBoxFileWriter(
            data=data,
            target_path=Path("sample"),
            timestamp=123.0,
            metadata_store=metadata_store,
        )

        assert writer.write() is True
        srs_path = tmp_path / "sing-box" / "sample.srs"
        actual = srs_path.read_bytes()

        assert zlib.decompress(actual[4:]) == zlib.decompress(reference[4:])
        assert {record.path for record in metadata_store.data} == {
            Path("sing-box/sample.json"),
            Path("sing-box/sample.srs"),
        }
