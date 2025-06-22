import validators
import tldextract

from config import LOGICAL_KEYWORDS, LOGICAL_AND_OR, LOGICAL_NOT


def is_logical_keyword(logical: str) -> bool:
    return logical.upper() in LOGICAL_KEYWORDS


def is_logical_and_or(logical: str) -> bool:
    return logical.upper() in LOGICAL_AND_OR


def is_logical_not(logical: str) -> bool:
    return logical.upper() == LOGICAL_NOT


def validate_domain(domain: str) -> bool:
    if "." not in domain:
        return True
    return validators.domain(domain, rfc_2782=True)


def is_eTLD(domain: str) -> bool:
    result = tldextract.extract(domain)
    return domain == result.suffix
