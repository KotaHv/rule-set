import json
import zlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from rule_set.config import settings
from rule_set.errors import SerializerError
from rule_set.file_writers import write_if_changed
from rule_set.output import SING_BOX_SRS_OUTPUT
from rule_set.serializers.clients.sing_box import SingBoxSrsSerializer
from rule_set.serializers.encoding.binary import ByteWriter
from rule_set.serializers.srs import encode_rule_set
from rule_set.serializers.srs.rules import RuleSetSource

FIXTURES = Path(__file__).parent / "fixtures" / "srs"


@pytest.mark.parametrize(
    "source_path",
    sorted(FIXTURES.glob("*.json")),
    ids=lambda path: path.stem,
)
def test_srs_matches_sing_box_reference(source_path: Path) -> None:
    reference = source_path.with_suffix(".srs").read_bytes()
    rule_set = json.loads(source_path.read_text(encoding="utf-8"))
    actual = encode_rule_set(rule_set)

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
    source = RuleSetSource.model_validate(
        {"version": 5, "rules": [{"domain": ["example.com"]}]}
    )

    assert encode_rule_set(source)[3] == 2


def test_rejects_unknown_rule_fields() -> None:
    with pytest.raises(ValidationError):
        _ = RuleSetSource.model_validate(
            {"version": 2, "rules": [{"adguard_domain": ["||ads.example^"]}]}
        )


def test_rejects_network_type_before_version_3() -> None:
    source = RuleSetSource.model_validate(
        {"version": 2, "rules": [{"network_type": ["wifi"]}]}
    )

    with pytest.raises(SerializerError, match="version 3"):
        _ = encode_rule_set(source)


def test_rejects_package_name_regex_before_version_5() -> None:
    source = RuleSetSource.model_validate(
        {"version": 2, "rules": [{"package_name_regex": ["^com"]}]}
    )

    with pytest.raises(SerializerError, match="version 5"):
        _ = encode_rule_set(source)


def test_rejects_unknown_network_type() -> None:
    with pytest.raises(ValidationError):
        _ = RuleSetSource.model_validate(
            {"version": 3, "rules": [{"network_type": ["bluetooth"]}]}
        )


def test_rejects_empty_logical_rule() -> None:
    with pytest.raises(ValidationError):
        _ = RuleSetSource.model_validate(
            {"version": 2, "rules": [{"type": "logical", "mode": "and", "rules": []}]}
        )


def test_rejects_empty_domain_item() -> None:
    source = RuleSetSource.model_validate(
        {"version": 2, "rules": [{"domain_suffix": [""]}]}
    )

    with pytest.raises(SerializerError, match="domain_suffix"):
        _ = encode_rule_set(source)


def test_rejects_invalid_ip_cidr() -> None:
    source = RuleSetSource.model_validate(
        {"version": 2, "rules": [{"ip_cidr": ["not-a-cidr"]}]}
    )

    with pytest.raises(SerializerError, match="invalid ip_cidr"):
        _ = encode_rule_set(source)


@pytest.mark.parametrize(
    "payload",
    [
        {"version": 2, "rules": [{"query_type": True}]},
        {"version": 2, "rules": [{"query_type": [True]}]},
        {"version": 2, "rules": [{"source_port": False}]},
        {"version": 2, "rules": [{"port": [False]}]},
    ],
)
def test_rejects_boolean_uint16_values(payload: object) -> None:
    with pytest.raises(ValidationError):
        _ = RuleSetSource.model_validate(payload)


def _fail_subprocess(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("the SRS writer must not invoke an external process")


def test_srs_writer_generates_srs_without_sing_box(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "build_dir", tmp_path)
    monkeypatch.setattr("subprocess.run", _fail_subprocess)
    data = (FIXTURES / "logical.json").read_text(encoding="utf-8")
    rule_set = json.loads(data)
    reference = (FIXTURES / "logical.srs").read_bytes()
    srs_path = SING_BOX_SRS_OUTPUT.path(Path("sample"))

    assert (
        write_if_changed(srs_path, SingBoxSrsSerializer().serialize(rule_set)) is True
    )
    assert srs_path == tmp_path / "sing-box" / "sample.srs"
    actual = srs_path.read_bytes()

    assert zlib.decompress(actual[4:]) == zlib.decompress(reference[4:])
