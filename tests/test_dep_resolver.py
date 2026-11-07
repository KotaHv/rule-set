from pathlib import Path

import pytest

from rule_set.models import SourceModel, SourceReference
from rule_set.sources.dep_resolver import DependencyResolver


def _source(name: str, *dependencies: str) -> SourceModel:
    return SourceModel(
        name=Path(name),
        resources=[SourceReference(target=dependency) for dependency in dependencies],
    )


def _resolved_names(sources: list[SourceModel]) -> list[str]:
    return [str(source.name) for source in DependencyResolver(sources).resolve_order()]


def test_resolve_order_places_dependencies_before_dependents():
    order = _resolved_names(
        [
            _source("app", "api"),
            _source("api", "base"),
            _source("base"),
        ]
    )

    assert set(order) == {"app", "api", "base"}
    assert order.index("base") < order.index("api") < order.index("app")


def test_resolve_order_handles_diamond_dependencies():
    resolver = DependencyResolver(
        [
            _source("app", "left", "right"),
            _source("left", "base"),
            _source("right", "base"),
            _source("base"),
        ]
    )
    order = [str(source.name) for source in resolver.resolve_order()]

    assert set(order) == {"app", "left", "right", "base"}
    assert order.index("base") < order.index("left") < order.index("app")
    assert order.index("base") < order.index("right") < order.index("app")
    assert resolver.get_dependencies("app") == {"left", "right"}
    assert resolver.get_all_dependencies("app") == {"left", "right", "base"}


def test_unknown_source_raises_value_error():
    with pytest.raises(ValueError, match="references unknown source 'missing'"):
        _ = DependencyResolver([_source("app", "missing")])


def test_circular_dependency_raises_value_error():
    resolver = DependencyResolver(
        [
            _source("a", "b"),
            _source("b", "a"),
        ]
    )

    with pytest.raises(ValueError, match="Circular dependencies detected"):
        _ = resolver.resolve_order()
