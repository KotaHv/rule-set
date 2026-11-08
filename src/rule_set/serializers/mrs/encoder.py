"""MRS container encoding.

Invalid rules raise SerializerError instead of being logged and skipped as
mihomo's converter does: silently dropping a rule can weaken a generated
rule-set.
"""

from compression import zstd
from typing import Literal

from rule_set.errors import SerializerError

from ..encoding.binary import ByteWriter
from .domain import encode_domain_set
from .ip import encode_ip_set

MrsBehavior = Literal["domain", "ipcidr"]

_MRS_MAGIC = b"MRS\x01"
_BEHAVIOR_BYTES: dict[MrsBehavior, int] = {"domain": 0, "ipcidr": 1}
_ZSTD_LEVEL = 3


def _encode(payload: list[str], *, behavior: MrsBehavior) -> bytes:
    if not payload:
        raise SerializerError("empty rule")

    body = (
        encode_domain_set(payload) if behavior == "domain" else encode_ip_set(payload)
    )

    writer = ByteWriter()
    writer.write_bytes(_MRS_MAGIC)
    writer.write_byte(_BEHAVIOR_BYTES[behavior])
    writer.write_int64_be(len(payload))
    writer.write_int64_be(0)
    writer.write_bytes(body)
    return zstd.compress(writer.to_bytes(), level=_ZSTD_LEVEL)


def encode_domain(payload: list[str]) -> bytes:
    return _encode(payload, behavior="domain")


def encode_ipcidr(payload: list[str]) -> bytes:
    return _encode(payload, behavior="ipcidr")
