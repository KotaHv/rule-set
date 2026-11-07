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
from rule_set.serializers.clients.clash import ClashSerializer
from rule_set.serializers.clients.loon import LoonSerializer
from rule_set.serializers.clients.sing_box import SingBoxSerializer
from rule_set.serializers.clients.surge import SurgeSerializer
from rule_set.serializers.clients.v2ray_geo_ip import GeoIPSerializer
from rule_set.serializers.v2ray_geo_ip import geo_ip_pb2


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


def _payload(artifact) -> list[str]:
    data = yaml.safe_load(artifact.data)
    return data["payload"]


def test_clash_splits_rules_into_domain_ipcidr_and_classical_artifacts():
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

    artifacts = ClashSerializer(rules=rules, option=Option()).serialize()
    by_kind = {artifact.kind: artifact for artifact in artifacts}

    assert set(by_kind) == {
        ArtifactKind.DOMAIN,
        ArtifactKind.IPCIDR,
        ArtifactKind.CLASSICAL,
    }
    assert set(_payload(by_kind[ArtifactKind.DOMAIN])) == {
        "example.com",
        "+.example.net",
    }
    assert set(_payload(by_kind[ArtifactKind.IPCIDR])) == {
        "1.1.1.0/24",
        "2001:db8::/32",
    }
    assert set(_payload(by_kind[ArtifactKind.CLASSICAL])) == {
        "DOMAIN-WILDCARD,*.example.org",
        r"DOMAIN-REGEX,^ads\.",
        "DOMAIN-KEYWORD,ads",
        "IP-ASN,13335,no-resolve",
        "PROCESS-NAME,curl",
        "AND,((DOMAIN-SUFFIX,example.com),(DOMAIN-KEYWORD,ads))",
    }

    geo_ip_artifacts = ClashSerializer(
        rules=rules,
        option=Option(geo_ip=GeoIPOption(country_code="CN")),
    ).serialize()
    assert {artifact.kind for artifact in geo_ip_artifacts} == {
        ArtifactKind.DOMAIN,
        ArtifactKind.IPCIDR,
        ArtifactKind.CLASSICAL,
    }


@pytest.mark.parametrize(
    ("no_resolve", "expected_asn"),
    [
        (True, "IP-ASN,13335,no-resolve"),
        (False, "IP-ASN,13335"),
    ],
)
def test_clash_honors_no_resolve_for_asn(no_resolve, expected_asn):
    rules = SerializableRuleModel(
        domain=["example.com"],
        ip_asn=["13335"],
    )

    artifacts = ClashSerializer(
        rules=rules,
        option=Option(serialization=SerializationOption(no_resolve=no_resolve)),
    ).serialize()
    classical = next(
        artifact for artifact in artifacts if artifact.kind == ArtifactKind.CLASSICAL
    )

    assert expected_asn in _payload(classical)


TEXT_SERIALIZERS = [SurgeSerializer, LoonSerializer]


@pytest.mark.parametrize("serializer_type", TEXT_SERIALIZERS)
def test_text_serializers_convert_domain_regex_to_wildcard(serializer_type):
    rules = SerializableRuleModel(domain_regex=[r"^ads-[0-9]\.example\.com$"])

    data = serializer_type(rules=rules, option=Option()).serialize()[0].data

    assert "DOMAIN-WILDCARD,ads-[0-9].example.com" in data.splitlines()


@pytest.mark.parametrize("serializer_type", TEXT_SERIALIZERS)
def test_text_serializers_return_empty_content_for_no_rules(serializer_type):
    artifact = serializer_type(
        rules=SerializableRuleModel(),
        option=Option(),
    ).serialize()[0]

    assert artifact.kind == ArtifactKind.DEFAULT
    assert artifact.data == ""


@pytest.mark.parametrize(
    ("no_resolve", "suffix"),
    [
        (True, ",no-resolve"),
        (False, ""),
    ],
)
def test_surge_honors_no_resolve_for_ip_and_asn(no_resolve, suffix):
    rules = SerializableRuleModel(
        ip_cidr=["1.1.1.0/24"],
        ip_cidr6=["2001:db8::/32"],
        ip_asn=["13335"],
    )

    data = (
        SurgeSerializer(
            rules=rules,
            option=Option(serialization=SerializationOption(no_resolve=no_resolve)),
        )
        .serialize()[0]
        .data
    )
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

    data = json.loads(
        SingBoxSerializer(rules=rules, option=Option()).serialize()[0].data
    )
    first_rule = data["rules"][0]

    assert data["version"] == 2
    assert first_rule["domain"] == ["example.com"]
    assert set(first_rule["domain_regex"]) == {
        r"^.*\.example\.org$",
        r"^ads\.",
    }
    assert set(first_rule["ip_cidr"]) == {
        "1.1.1.0/24",
        "2001:db8::/32",
    }
    assert first_rule["domain_keyword"] == ["ads"]
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

    data = json.loads(
        SingBoxSerializer(rules=rules, option=Option()).serialize()[0].data
    )

    assert data["rules"][0]["ip_cidr"] == ["2001:db8::/32"]


def test_sing_box_does_not_mutate_ip_cidr_when_merging():
    rules = SerializableRuleModel(
        ip_cidr=["1.1.1.0/24"],
        ip_cidr6=["2001:db8::/32"],
    )

    SingBoxSerializer(rules=rules, option=Option()).serialize()

    assert rules.ip_cidr == ["1.1.1.0/24"]


def test_geo_ip_serializer_encodes_country_and_network_prefixes():
    rules = SerializableRuleModel(
        ip_cidr=["1.1.1.0/24"],
        ip_cidr6=["2001:db8::/32"],
    )

    data = (
        GeoIPSerializer(
            rules=rules,
            option=Option(geo_ip=GeoIPOption(country_code="CN")),
        )
        .serialize()[0]
        .data
    )

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
        GeoIPSerializer(rules=rules, option=Option()).serialize()
