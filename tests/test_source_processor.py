from pathlib import Path

import pytest

from rule_set.cache import Cache
from rule_set.config import settings
from rule_set.metadata import MetadataStore
from rule_set.models import (
    GeoIPOption,
    Option,
    RuleModel,
    SerializeFormat,
    SourceModel,
)
from rule_set.models.sing_box import SingBoxRuleSet
from rule_set.processors.resource import ResourceProcessor
from rule_set.processors.source import SourceProcessor
from rule_set.serializers.clients.clash import ClashMrsSerializer, ClashPayload
from rule_set.serializers.clients.sing_box import SingBoxSrsSerializer


def _rules(domain: str = "example.com") -> RuleModel:
    return RuleModel(domain={domain}, ip_cidr={"1.1.1.0/24"})


@pytest.fixture
def processor_factory(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "build_dir", tmp_path / "build")
    monkeypatch.setattr(settings, "metadata_path", tmp_path / "metadata.db")
    monkeypatch.setattr(settings, "cache_dir", tmp_path / "cache")

    source_cache = Cache(path="source")
    _ = source_cache.store("sample", _rules().model_dump_json())

    with MetadataStore() as metadata_store:
        processor = SourceProcessor(
            cache=source_cache,
            resource_processor=ResourceProcessor(Cache(path="resource")),
            metadata_store=metadata_store,
        )
        yield processor, metadata_store


@pytest.mark.parametrize(
    ("serialize_format", "relative_path"),
    [
        (SerializeFormat.Surge, Path("surge/sample.list")),
        (SerializeFormat.Loon, Path("loon/sample.list")),
        (SerializeFormat.Egern, Path("egern/sample.yaml")),
        (SerializeFormat.GeoIP, Path("geoip/sample.dat")),
    ],
)
def test_single_file_formats_are_written(
    processor_factory, serialize_format, relative_path
):
    processor, metadata_store = processor_factory
    source = SourceModel(
        resources=[],
        name=Path("sample"),
        include=[serialize_format],
        option=Option(geo_ip=GeoIPOption(country_code="CN")),
    )

    processor.build(source)

    assert (settings.build_dir / relative_path).is_file()
    assert {record.path for record in metadata_store.data} == {relative_path}


def test_clash_classical_output_has_no_mrs(processor_factory):
    processor, metadata_store = processor_factory
    rules = RuleModel()
    rules.domain_keyword.add("ads")
    _ = processor.cache.store("sample", rules.model_dump_json())
    source = SourceModel(
        resources=[],
        name=Path("sample"),
        include=[SerializeFormat.Clash],
    )

    processor.build(source)

    yaml_path = settings.build_dir / "clash" / "classical" / "sample.yaml"
    assert yaml_path.is_file()
    assert not yaml_path.with_suffix(".mrs").exists()
    assert {record.path for record in metadata_store.data} == {
        Path("clash/classical/sample.yaml"),
    }


def test_sing_box_outputs_are_generated_lazily(processor_factory, monkeypatch):
    processor, metadata_store = processor_factory
    source = SourceModel(
        resources=[],
        name=Path("sample"),
        include=[SerializeFormat.Sing_Box],
    )
    encode_calls = 0
    original = SingBoxSrsSerializer.serialize

    def spy(self: SingBoxSrsSerializer, rule_set: SingBoxRuleSet) -> bytes:
        nonlocal encode_calls
        encode_calls += 1
        return original(self, rule_set)

    monkeypatch.setattr(SingBoxSrsSerializer, "serialize", spy)

    processor.build(source)

    json_path = settings.build_dir / "sing-box" / "sample.json"
    srs_path = settings.build_dir / "sing-box" / "sample.srs"
    assert json_path.exists()
    assert srs_path.exists()
    assert encode_calls == 1
    assert {record.path for record in metadata_store.data} == {
        Path("sing-box/sample.json"),
        Path("sing-box/sample.srs"),
    }

    processor.build(source)

    assert encode_calls == 1

    srs_path.unlink()
    processor.build(source)

    assert encode_calls == 2
    assert srs_path.exists()

    _ = processor.cache.store("sample", _rules("changed.example").model_dump_json())
    processor.build(source)

    assert encode_calls == 3
    assert "changed.example" in json_path.read_text(encoding="utf-8")


def test_clash_outputs_are_generated_lazily(processor_factory, monkeypatch):
    processor, metadata_store = processor_factory
    source = SourceModel(
        resources=[],
        name=Path("sample"),
        include=[SerializeFormat.Clash],
    )
    encode_calls = 0
    original = ClashMrsSerializer.serialize

    def spy(self: ClashMrsSerializer, payload: ClashPayload) -> bytes:
        nonlocal encode_calls
        encode_calls += 1
        return original(self, payload)

    monkeypatch.setattr(ClashMrsSerializer, "serialize", spy)

    processor.build(source)

    domain_mrs = settings.build_dir / "clash" / "domain" / "sample.mrs"
    ipcidr_mrs = settings.build_dir / "clash" / "ipcidr" / "sample.mrs"
    assert (settings.build_dir / "clash" / "domain" / "sample.yaml").exists()
    assert (settings.build_dir / "clash" / "ipcidr" / "sample.yaml").exists()
    assert domain_mrs.exists()
    assert ipcidr_mrs.exists()
    assert encode_calls == 2
    assert {record.path for record in metadata_store.data} == {
        Path("clash/domain/sample.yaml"),
        Path("clash/domain/sample.mrs"),
        Path("clash/ipcidr/sample.yaml"),
        Path("clash/ipcidr/sample.mrs"),
    }

    processor.build(source)

    assert encode_calls == 2

    domain_mrs.unlink()
    processor.build(source)

    assert encode_calls == 3
    assert domain_mrs.exists()
