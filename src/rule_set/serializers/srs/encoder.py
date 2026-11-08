import zlib

from rule_set.models.sing_box import SingBoxRuleSet

from ..encoding.binary import ByteWriter
from .rules import RuleSetSource, encode_payload, output_version


def encode_rule_set(source: SingBoxRuleSet | RuleSetSource) -> bytes:
    rule_set = (
        source
        if isinstance(source, RuleSetSource)
        else RuleSetSource.model_validate(source)
    )
    version = output_version(rule_set)

    writer = ByteWriter()
    writer.write_bytes(b"SRS")
    writer.write_byte(version)
    writer.write_bytes(zlib.compress(encode_payload(rule_set, version), level=9))
    return writer.to_bytes()
