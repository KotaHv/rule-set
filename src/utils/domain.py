import re
import re._parser as sre_parser

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


def regex_to_wildcard(domain_regex: str) -> list[str]:
    ast = sre_parser.parse(domain_regex)
    return _ast_to_wildcard(ast)


_star_re = re.compile(r"\*+")


def merge_star(s: str) -> str:
    return _star_re.sub("*", s)


_leading_wildcard_re = re.compile(r"^\?\*\.")


def fix_leading_wildcard(s: str) -> str:
    return _leading_wildcard_re.sub("*.", s)


def _ast_to_wildcard(ast: sre_parser.SubPattern) -> list[str]:
    wildcards = [""]
    for op, arg in ast:
        if op in (sre_parser.MAX_REPEAT, sre_parser.MIN_REPEAT):
            min_r, max_r, sub_pattern = arg
            sub_wildcards = _ast_to_wildcard(sub_pattern)
            new_wildcards = []
            for w in wildcards:
                for sw in sub_wildcards:
                    if min_r == max_r:
                        new_wildcards.append(w + sw * min_r)
                    elif max_r == sre_parser.MAXREPEAT:
                        new_wildcards.append(
                            w + (sw * min_r + "*" if min_r > 1 else "*")
                        )
                    else:
                        new_wildcards.extend(
                            (w + sw * i for i in range(min_r, max_r + 1))
                            if max_r - min_r <= 5
                            else [w + sw * min_r + "*"]
                        )
            wildcards = new_wildcards
        elif op == sre_parser.LITERAL:
            char = chr(arg)
            wildcards = [w + char for w in wildcards]
        elif op == sre_parser.IN:
            wildcards = [w + "?" for w in wildcards]
        elif op == sre_parser.ANY:
            wildcards = [w + "?" for w in wildcards]
        elif op == sre_parser.SUBPATTERN:
            sub_wildcards = _ast_to_wildcard(arg[-1])
            wildcards = [w + sw for w in wildcards for sw in sub_wildcards]
        elif op == sre_parser.BRANCH:
            wildcards = [w + "*" for w in wildcards]
        elif op == sre_parser.AT:
            continue
    for i, w in enumerate(wildcards):
        w_clean = merge_star(w)
        w_clean = fix_leading_wildcard(w_clean)
        wildcards[i] = w_clean
    return wildcards
