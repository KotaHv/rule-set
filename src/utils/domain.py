import validators
import tldextract


def validate_domain(domain: str) -> bool:
    """Validate domain format."""
    if "." not in domain:
        return True
    return validators.domain(domain, rfc_2782=True)


def is_eTLD(domain: str) -> bool:
    """Check if domain is an effective TLD."""
    result = tldextract.extract(domain)
    return domain == result.suffix


def wildcard_to_regex(domain_wildcard: str) -> str:
    """Convert domain wildcard pattern to regex pattern."""
    domain_regex = (
        domain_wildcard.replace(".", r"\.")
        .replace("?", r"[\w.-]")
        .replace("*", r"[\w.-]*?")
    )
    return f"^{domain_regex}$"


def domain_to_regex(domain: str) -> str:
    domain_regex = domain.replace(".", r"\.")
    return f"^{domain_regex}$"


def suffix_to_regex(domain_suffix: str) -> str:
    domain_regex = domain_suffix.replace(".", r"\.")
    return rf"[\w.-]*?\.{domain_regex}$"


def keyword_to_regex(domain_keyword: str) -> str:
    domain_regex = domain_keyword.replace(".", r"\.")
    return domain_regex
