import hashlib
from typing import Any
from urllib.parse import urlparse, urlunparse

import validators
import tldextract
from pydantic import HttpUrl


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


def build_v2ray_include_url(base_url: HttpUrl, include: str) -> HttpUrl:
    parsed = urlparse(str(base_url))
    new_path = parsed.path.rsplit("/", 1)[0] + f"/{include}"

    new_url = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            new_path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )
    return HttpUrl(new_url)


def generate_cache_key(key: Any) -> str:
    return hashlib.sha256(str(key).encode()).hexdigest()
