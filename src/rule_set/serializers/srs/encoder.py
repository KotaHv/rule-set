import zlib

from ..encoding.binary import ByteWriter
from .rules import RuleSetSource, encode_payload, output_version


def encode_rule_set(source: str | bytes) -> bytes:
    rule_set = RuleSetSource.model_validate_json(source)
    version = output_version(rule_set)

    writer = ByteWriter()
    writer.write_bytes(b"SRS")
    writer.write_byte(version)
    writer.write_bytes(zlib.compress(encode_payload(rule_set, version), level=9))
    return writer.to_bytes()
