import re
import re._parser as sre_parser

import tldextract
import validators


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
    parsed_pattern = sre_parser.parse(domain_regex)
    return _ast_to_wildcard(parsed_pattern)


_star_re = re.compile(r"\*+")


def merge_star(s: str) -> str:
    return _star_re.sub("*", s)


_leading_wildcard_re = re.compile(r"^\?\*\.")


def fix_leading_wildcard(s: str) -> str:
    return _leading_wildcard_re.sub("*.", s)


def _ast_to_wildcard(parsed_pattern: sre_parser.SubPattern) -> list[str]:
    wildcards = [""]
    for token_type, token_value in parsed_pattern:
        if token_type in (sre_parser.MAX_REPEAT, sre_parser.MIN_REPEAT):
            min_repetitions, max_repetitions, sub_pattern = token_value
            sub_wildcards = _ast_to_wildcard(sub_pattern)
            new_wildcards = []
            for wildcard_prefix in wildcards:
                for subpattern_wildcard in sub_wildcards:
                    if min_repetitions == max_repetitions:
                        new_wildcards.append(
                            wildcard_prefix + subpattern_wildcard * min_repetitions
                        )
                    elif max_repetitions == sre_parser.MAXREPEAT:
                        new_wildcards.append(
                            wildcard_prefix
                            + (
                                subpattern_wildcard * min_repetitions + "*"
                                if min_repetitions > 1
                                else "*"
                            )
                        )
                    else:
                        new_wildcards.extend(
                            (
                                wildcard_prefix + subpattern_wildcard * repetitions
                                for repetitions in range(
                                    min_repetitions, max_repetitions + 1
                                )
                            )
                            if max_repetitions - min_repetitions <= 5
                            else [
                                wildcard_prefix
                                + subpattern_wildcard * min_repetitions
                                + "*"
                            ]
                        )
            wildcards = new_wildcards
        elif token_type == sre_parser.LITERAL:
            literal_character = chr(token_value)
            wildcards = [wildcard + literal_character for wildcard in wildcards]
        elif token_type == sre_parser.IN:
            wildcards = [wildcard + "?" for wildcard in wildcards]
        elif token_type == sre_parser.ANY:
            wildcards = [wildcard + "?" for wildcard in wildcards]
        elif token_type == sre_parser.SUBPATTERN:
            sub_wildcards = _ast_to_wildcard(token_value[-1])
            wildcards = [
                wildcard_prefix + subpattern_wildcard
                for wildcard_prefix in wildcards
                for subpattern_wildcard in sub_wildcards
            ]
        elif token_type == sre_parser.BRANCH:
            wildcards = [wildcard + "*" for wildcard in wildcards]
        elif token_type == sre_parser.AT:
            continue
    for wildcard_index, wildcard in enumerate(wildcards):
        normalized_wildcard = merge_star(wildcard)
        normalized_wildcard = fix_leading_wildcard(normalized_wildcard)
        wildcards[wildcard_index] = normalized_wildcard
    return wildcards
