import pytest

from rule_set.utils import validate_domain


@pytest.mark.parametrize(
    "domain",
    [
        "example.com",
        "xn----gtbspbbmkef.xn--p1aic",
        "localhost",
    ],
)
def test_validate_domain_accepts_valid_domains(domain: str) -> None:
    assert validate_domain(domain) is True


@pytest.mark.parametrize(
    "domain",
    [
        "",
        " \t ",
        "-bad.example",
        "example..com",
        "domain:",
        "unknown:value",
        "-bad",
    ],
)
def test_validate_domain_rejects_invalid_domains(domain: str) -> None:
    assert validate_domain(domain) is False
