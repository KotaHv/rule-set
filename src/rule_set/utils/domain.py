import re

import tldextract
import validators

from .re_parser import parse_regex_to_wildcards


def validate_domain(domain: str) -> bool:
    """Validate domain format."""
    if "." not in domain:
        return True
    return validators.domain(domain, rfc_2782=True) is True


def is_eTLD(domain: str) -> bool:
    """Check if domain is an effective TLD."""
    result = tldextract.extract(domain)
    return domain == result.suffix


def wildcard_to_regex(domain_wildcard: str) -> str:
    """Convert domain wildcard pattern to regex pattern."""
    parts: list[str] = []
    index, length = 0, len(domain_wildcard)
    while index < length:
        char = domain_wildcard[index]
        if char == "*":
            parts.append(".*")
            index += 1
        elif char == "?":
            parts.append(".")
            index += 1
        elif char == "[":
            end = domain_wildcard.find("]", index + 1)
            if end == -1:
                raise ValueError(f"unclosed '[' in {domain_wildcard!r}")
            content = domain_wildcard[index + 1 : end]
            if not content or content in ("!", "^"):
                raise ValueError(f"empty character class in {domain_wildcard!r}")
            if "[" in content or "\\" in content:
                raise ValueError(f"unsupported character class in {domain_wildcard!r}")
            if content.startswith("!"):
                content = "^" + content[1:]
            parts.append(f"[{content}]")
            index = end + 1
        else:
            parts.append(re.escape(char))
            index += 1
    return f"^{''.join(parts)}$"


def regex_to_wildcard(domain_regex: str) -> list[str]:
    return parse_regex_to_wildcards(domain_regex)
