import struct
from compression import zstd
from pathlib import Path

import pytest

from rule_set.config import settings
from rule_set.errors import SerializerError
from rule_set.file_writers.base import BaseFileWriter
from rule_set.file_writers.clash import ClashDomainFileWriter, ClashIpcidrFileWriter
from rule_set.metadata import MetadataStore
from rule_set.serializers.mrs import MrsBehavior, encode_rule_set

FIXTURES = Path(__file__).parent / "fixtures" / "mrs"

_MRS_MAGIC = b"MRS\x01"
_BEHAVIOR_BYTES: dict[MrsBehavior, int] = {"domain": 0, "ipcidr": 1}


@pytest.mark.parametrize(
    ("behavior", "stem"),
    [
        ("domain", "domain"),
        ("domain", "domain_unicode"),
        ("ipcidr", "ipcidr"),
    ],
)
def test_mrs_matches_mihomo_reference(behavior: MrsBehavior, stem: str) -> None:
    source = (FIXTURES / f"{stem}.yaml").read_bytes()
    reference = (FIXTURES / f"{stem}.mrs").read_bytes()
    actual = encode_rule_set(source, behavior=behavior)
    actual_payload = zstd.decompress(actual)
    reference_payload = zstd.decompress(reference)

    assert actual_payload == reference_payload
    assert actual_payload[:4] == _MRS_MAGIC
    assert actual_payload[4] == _BEHAVIOR_BYTES[behavior]


def test_count_uses_source_rule_count() -> None:
    source = "payload:\n- example.com\n- example.com\n- '+.example.com'\n"
    payload = zstd.decompress(encode_rule_set(source, behavior="domain"))
    count = struct.unpack(">q", payload[5:13])[0]

    assert count == 3


@pytest.mark.parametrize("source", ["payload: []\n", "rules: []\n"])
def test_rejects_empty_rule_set(source: str) -> None:
    with pytest.raises(SerializerError, match="empty rule"):
        _ = encode_rule_set(source, behavior="domain")


@pytest.mark.parametrize(
    "domain",
    [
        "a..b",
        "example.com.",
        "wrong*.example.com",
        "+.+",
    ],
)
def test_rejects_invalid_domain(domain: str) -> None:
    source = f"payload:\n- '{domain}'\n"
    with pytest.raises(SerializerError, match="invalid domain"):
        _ = encode_rule_set(source, behavior="domain")


def test_rejects_invalid_ip_cidr() -> None:
    with pytest.raises(SerializerError, match="invalid ip_cidr"):
        _ = encode_rule_set("payload:\n- not-a-cidr\n", behavior="ipcidr")


def _fail_subprocess(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("the MRS writer must not invoke an external process")


@pytest.mark.parametrize(
    ("writer_type", "behavior", "stem"),
    [
        (ClashDomainFileWriter, "domain", "domain"),
        (ClashIpcidrFileWriter, "ipcidr", "ipcidr"),
    ],
)
def test_file_writer_generates_mrs_without_mihomo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    writer_type: type[BaseFileWriter],
    behavior: MrsBehavior,
    stem: str,
) -> None:
    monkeypatch.setattr(settings, "build_dir", tmp_path)
    monkeypatch.setattr(settings, "metadata_path", tmp_path / "metadata.db")
    monkeypatch.setattr("subprocess.run", _fail_subprocess)
    data = (FIXTURES / f"{stem}.yaml").read_text(encoding="utf-8")
    reference = (FIXTURES / f"{stem}.mrs").read_bytes()

    with MetadataStore() as metadata_store:
        writer = writer_type(
            data=data,
            target_path=Path("sample"),
            timestamp=123.0,
            metadata_store=metadata_store,
        )

        assert writer.write() is True
        mrs_path = tmp_path / "clash" / behavior / "sample.mrs"
        actual = mrs_path.read_bytes()

        assert zstd.decompress(actual) == zstd.decompress(reference)
        assert {record.path for record in metadata_store.data} == {
            Path(f"clash/{behavior}/sample.yaml"),
            Path(f"clash/{behavior}/sample.mrs"),
        }
