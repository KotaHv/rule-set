import ipaddress
import json

import pytest
import yaml

from rule_set.errors import SerializerError
from rule_set.models import (
    ArtifactKind,
    GeoIPOption,
    Option,
    SerializableRuleModel,
    SerializationOption,
)
from rule_set.models.logical import (
    ConcreteRule,
    Logical,
    LogicalOperator,
    LogicalTree,
    Rule,
    RuleType,
)
from rule_set.models.sing_box import SingBoxRuleSet
from rule_set.serializers.clients.base import BaseRuleSerializer
from rule_set.serializers.clients.clash import (
    ClashMrsSerializer,
    ClashPayload,
    ClashPayloadSerializer,
    ClashYamlSerializer,
)
from rule_set.serializers.clients.loon import LoonSerializer
from rule_set.serializers.clients.sing_box import (
    SingBoxJsonSerializer,
    SingBoxRuleSetSerializer,
)
from rule_set.serializers.clients.surge import SurgeSerializer
from rule_set.serializers.clients.v2ray_geo_ip import GeoIPSerializer
from rule_set.serializers.v2ray_geo_ip import geo_ip_pb2

LAST_UPDATED = "2026-01-01T00:00:00+00:00"


def _logical_tree() -> LogicalTree:
    return LogicalTree(
        root=Logical(
            op=LogicalOperator.AND,
            children=(
                Rule(
                    rule=ConcreteRule(
                        rule_type=RuleType.DOMAIN_SUFFIX,
                        rule_values=("example.com",),
                    )
                ),
                Rule(
                    rule=ConcreteRule(
                        rule_type=RuleType.DOMAIN_KEYWORD,
                        rule_values=("ads",),
                    )
                ),
            ),
        )
    )


def _clash_payloads(
    rules: SerializableRuleModel, option: Option | None = None
) -> list[ClashPayload]:
    return ClashPayloadSerializer(
        option=option or Option(),
        last_updated=LAST_UPDATED,
    ).serialize(rules)


def test_clash_splits_rules_into_domain_ipcidr_and_classical_payloads():
    rules = SerializableRuleModel(
        domain=["example.com"],
        domain_suffix=["example.net"],
        domain_wildcard=["*.example.org"],
        domain_regex=[r"^ads\."],
        domain_keyword=["ads"],
        ip_cidr=["1.1.1.0/24"],
        ip_cidr6=["2001:db8::/32"],
        ip_asn=["13335"],
        process=["curl"],
        logical=[_logical_tree()],
    )

    payloads = _clash_payloads(rules)
    by_kind = {payload.kind: payload for payload in payloads}

    assert set(by_kind) == {
        ArtifactKind.DOMAIN,
        ArtifactKind.IPCIDR,
        ArtifactKind.CLASSICAL,
    }
    assert set(by_kind[ArtifactKind.DOMAIN].rules) == {
        "example.com",
        "+.example.net",
    }
    assert set(by_kind[ArtifactKind.IPCIDR].rules) == {
        "1.1.1.0/24",
        "2001:db8::/32",
    }
    assert set(by_kind[ArtifactKind.CLASSICAL].rules) == {
        "DOMAIN-WILDCARD,*.example.org",
        r"DOMAIN-REGEX,^ads\.",
        "DOMAIN-KEYWORD,ads",
        "IP-ASN,13335,no-resolve",
        "PROCESS-NAME,curl",
        "AND,((DOMAIN-SUFFIX,example.com),(DOMAIN-KEYWORD,ads))",
    }

    geo_ip_payloads = _clash_payloads(
        rules,
        Option(geo_ip=GeoIPOption(country_code="CN")),
    )
    assert {payload.kind for payload in geo_ip_payloads} == {
        ArtifactKind.DOMAIN,
        ArtifactKind.IPCIDR,
        ArtifactKind.CLASSICAL,
    }


def test_clash_domain_payload_preserves_unicode() -> None:
    domains = ["例子.测试", "BÜCHER.example"]
    payloads = _clash_payloads(SerializableRuleModel(domain=domains))
    domain = next(
        payload for payload in payloads if payload.kind == ArtifactKind.DOMAIN
    )

    assert domain.rules == domains


@pytest.mark.parametrize(
    ("no_resolve", "expected_asn"),
    [
        (True, "IP-ASN,13335,no-resolve"),
        (False, "IP-ASN,13335"),
    ],
)
def test_clash_honors_no_resolve_for_asn(no_resolve: bool, expected_asn: str) -> None:
    rules = SerializableRuleModel(
        domain=["example.com"],
        ip_asn=["13335"],
    )

    payloads = _clash_payloads(
        rules,
        Option(serialization=SerializationOption(no_resolve=no_resolve)),
    )
    classical = next(
        payload for payload in payloads if payload.kind == ArtifactKind.CLASSICAL
    )

    assert expected_asn in classical.rules


TEXT_SERIALIZERS: list[type[BaseRuleSerializer[str]]] = [
    SurgeSerializer,
    LoonSerializer,
]


@pytest.mark.parametrize("serializer_type", TEXT_SERIALIZERS)
def test_text_serializers_convert_domain_regex_to_wildcard(
    serializer_type: type[BaseRuleSerializer[str]],
) -> None:
    rules = SerializableRuleModel(domain_regex=[r"^ads-[0-9]\.example\.com$"])

    data = serializer_type(option=Option(), last_updated=LAST_UPDATED).serialize(rules)

    assert "DOMAIN-WILDCARD,ads-[0-9].example.com" in data.splitlines()


@pytest.mark.parametrize("serializer_type", TEXT_SERIALIZERS)
def test_text_serializers_return_empty_content_for_no_rules(
    serializer_type: type[BaseRuleSerializer[str]],
) -> None:
    data = serializer_type(option=Option(), last_updated=LAST_UPDATED).serialize(
        SerializableRuleModel()
    )

    assert data == ""


@pytest.mark.parametrize(
    ("no_resolve", "suffix"),
    [
        (True, ",no-resolve"),
        (False, ""),
    ],
)
def test_surge_honors_no_resolve_for_ip_and_asn(no_resolve: bool, suffix: str) -> None:
    rules = SerializableRuleModel(
        ip_cidr=["1.1.1.0/24"],
        ip_cidr6=["2001:db8::/32"],
        ip_asn=["13335"],
    )

    data = SurgeSerializer(
        option=Option(serialization=SerializationOption(no_resolve=no_resolve)),
        last_updated=LAST_UPDATED,
    ).serialize(rules)
    lines = set(data.splitlines())

    assert f"IP-CIDR,1.1.1.0/24{suffix}" in lines
    assert f"IP-CIDR6,2001:db8::/32{suffix}" in lines
    assert f"IP-ASN,13335{suffix}" in lines


def test_sing_box_merges_equivalent_fields_and_keeps_process_and_logical_separate():
    rules = SerializableRuleModel(
        domain=["example.com"],
        domain_wildcard=["*.example.org"],
        domain_regex=[r"^ads\."],
        domain_keyword=["ads"],
        ip_cidr=["1.1.1.0/24"],
        ip_cidr6=["2001:db8::/32"],
        process=["curl"],
        logical=[_logical_tree()],
    )

    rule_set = SingBoxRuleSetSerializer(
        option=Option(),
        last_updated=LAST_UPDATED,
    ).serialize(rules)
    data: SingBoxRuleSet = json.loads(SingBoxJsonSerializer().serialize(rule_set))
    first_rule = data["rules"][0]

    assert data["version"] == 2
    assert first_rule.get("domain") == ["example.com"]
    assert set(first_rule.get("domain_regex", [])) == {
        r"^.*\.example\.org$",
        r"^ads\.",
    }
    assert set(first_rule.get("ip_cidr", [])) == {
        "1.1.1.0/24",
        "2001:db8::/32",
    }
    assert first_rule.get("domain_keyword") == ["ads"]
    assert "process_name" not in first_rule
    assert {"process_name": ["curl"]} in data["rules"]
    assert data["rules"][-1] == {
        "type": "logical",
        "rules": [
            {"domain_suffix": "example.com"},
            {"domain_keyword": "ads"},
        ],
        "mode": "and",
    }


def test_sing_box_serializes_ipv6_only():
    rules = SerializableRuleModel(ip_cidr6=["2001:db8::/32"])

    rule_set = SingBoxRuleSetSerializer(
        option=Option(),
        last_updated=LAST_UPDATED,
    ).serialize(rules)
    data: SingBoxRuleSet = json.loads(SingBoxJsonSerializer().serialize(rule_set))

    assert data["rules"][0].get("ip_cidr") == ["2001:db8::/32"]


def test_sing_box_does_not_mutate_ip_cidr_when_merging():
    rules = SerializableRuleModel(
        ip_cidr=["1.1.1.0/24"],
        ip_cidr6=["2001:db8::/32"],
    )

    _ = SingBoxRuleSetSerializer(
        option=Option(),
        last_updated=LAST_UPDATED,
    ).serialize(rules)

    assert rules.ip_cidr == ["1.1.1.0/24"]


def test_clash_mrs_serializer_rejects_classical_payload() -> None:
    payload = ClashPayload(
        kind=ArtifactKind.CLASSICAL,
        rules=["DOMAIN-KEYWORD,ads"],
    )

    with pytest.raises(SerializerError, match="classical"):
        _ = ClashMrsSerializer().serialize(payload)


def test_clash_yaml_serializer_writes_domain_payload() -> None:
    payload = ClashPayload(kind=ArtifactKind.DOMAIN, rules=["example.com"])

    data = ClashYamlSerializer(last_updated=LAST_UPDATED).serialize(payload)

    assert data == (
        "# Total: 1 rules\n"
        f"# Last Updated: {LAST_UPDATED}\n"
        "'payload':\n"
        "- 'example.com'\n"
    )


def test_clash_yaml_serializer_writes_classical_payload() -> None:
    payload = ClashPayload(
        kind=ArtifactKind.CLASSICAL,
        rules=["DOMAIN-KEYWORD,ads"],
    )

    data = ClashYamlSerializer(last_updated=LAST_UPDATED).serialize(payload)
    lines = data.splitlines()

    assert lines[:2] == [
        "# Total: 1 rules",
        f"# Last Updated: {LAST_UPDATED}",
    ]
    assert yaml.safe_load("\n".join(lines[2:])) == {"payload": ["DOMAIN-KEYWORD,ads"]}


def test_sing_box_keeps_logical_rule_when_no_other_rules():
    rules = SerializableRuleModel(logical=[_logical_tree()])

    rule_set = SingBoxRuleSetSerializer(
        option=Option(),
        last_updated=LAST_UPDATED,
    ).serialize(rules)
    data: SingBoxRuleSet = json.loads(SingBoxJsonSerializer().serialize(rule_set))

    assert data == {
        "version": 2,
        "rules": [
            {
                "type": "logical",
                "rules": [
                    {"domain_suffix": "example.com"},
                    {"domain_keyword": "ads"},
                ],
                "mode": "and",
            }
        ],
    }


def test_geo_ip_serializer_encodes_country_and_network_prefixes():
    rules = SerializableRuleModel(
        ip_cidr=["1.1.1.0/24"],
        ip_cidr6=["2001:db8::/32"],
    )

    data = GeoIPSerializer(
        option=Option(geo_ip=GeoIPOption(country_code="CN")),
        last_updated=LAST_UPDATED,
    ).serialize(rules)

    assert isinstance(data, bytes)
    geo_ip_list = geo_ip_pb2.GeoIPList.FromString(data)
    entry = geo_ip_list.entry[0]

    assert entry.country_code == "CN"
    assert entry.inverse_match is False
    assert len(entry.cidr) == 2
    assert entry.cidr[0].ip == ipaddress.ip_network("1.1.1.0/24").network_address.packed
    assert entry.cidr[0].prefix == 24
    assert (
        entry.cidr[1].ip == ipaddress.ip_network("2001:db8::/32").network_address.packed
    )
    assert entry.cidr[1].prefix == 32


def test_geo_ip_serializer_requires_country_code():
    rules = SerializableRuleModel(ip_cidr=["1.1.1.0/24"])

    with pytest.raises(SerializerError, match="country code"):
        _ = GeoIPSerializer(option=Option(), last_updated=LAST_UPDATED).serialize(rules)
