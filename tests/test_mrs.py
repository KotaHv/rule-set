import struct
from compression import zstd
from pathlib import Path

import pytest
import yaml

from rule_set.config import settings
from rule_set.errors import SerializerError
from rule_set.file_writers import write_if_changed
from rule_set.models import ArtifactKind
from rule_set.output import CLASH_MRS_OUTPUTS
from rule_set.serializers.clients.clash import ClashMrsSerializer, ClashPayload
from rule_set.serializers.mrs import MrsBehavior, encode_domain, encode_ipcidr

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
    source = yaml.load(
        (FIXTURES / f"{stem}.yaml").read_bytes(), Loader=yaml.CSafeLoader
    )
    payload = source["payload"]
    reference = (FIXTURES / f"{stem}.mrs").read_bytes()
    encoder = encode_domain if behavior == "domain" else encode_ipcidr
    actual = encoder(payload)
    actual_payload = zstd.decompress(actual)
    reference_payload = zstd.decompress(reference)

    assert actual_payload == reference_payload
    assert actual_payload[:4] == _MRS_MAGIC
    assert actual_payload[4] == _BEHAVIOR_BYTES[behavior]


def test_count_includes_duplicate_domains() -> None:
    payload = ["example.com", "example.com", "+.example.com"]
    decoded = zstd.decompress(encode_domain(payload))
    count = struct.unpack(">q", decoded[5:13])[0]

    assert count == 3


@pytest.mark.parametrize("encoder", [encode_domain, encode_ipcidr])
def test_rejects_empty_rule_set(encoder) -> None:
    with pytest.raises(SerializerError, match="empty rule"):
        _ = encoder([])


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
    with pytest.raises(SerializerError, match="invalid domain"):
        _ = encode_domain([domain])


def test_rejects_invalid_ip_cidr() -> None:
    with pytest.raises(SerializerError, match="invalid ip_cidr"):
        _ = encode_ipcidr(["not-a-cidr"])


def _fail_subprocess(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("the MRS writer must not invoke an external process")


@pytest.mark.parametrize(
    ("kind", "behavior", "stem"),
    [
        (ArtifactKind.DOMAIN, "domain", "domain"),
        (ArtifactKind.IPCIDR, "ipcidr", "ipcidr"),
    ],
)
def test_mrs_writer_generates_mrs_without_mihomo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: ArtifactKind,
    behavior: MrsBehavior,
    stem: str,
) -> None:
    monkeypatch.setattr(settings, "build_dir", tmp_path)
    monkeypatch.setattr("subprocess.run", _fail_subprocess)
    source = yaml.load(
        (FIXTURES / f"{stem}.yaml").read_bytes(), Loader=yaml.CSafeLoader
    )
    payload = ClashPayload(kind=kind, rules=source["payload"])
    reference = (FIXTURES / f"{stem}.mrs").read_bytes()
    data = ClashMrsSerializer().serialize(payload)

    mrs_path = CLASH_MRS_OUTPUTS[kind].path(Path("sample"))

    assert write_if_changed(mrs_path, data) is True
    assert mrs_path == tmp_path / "clash" / behavior / "sample.mrs"
    actual = mrs_path.read_bytes()

    assert zstd.decompress(actual) == zstd.decompress(reference)
