import re
import re._parser as sre_parser

import tldextract
import validators


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
    parsed_pattern = sre_parser.parse(domain_regex)
    return _ast_to_wildcard(parsed_pattern)


_star_re = re.compile(r"\*+")


def merge_star(s: str) -> str:
    return _star_re.sub("*", s)


_leading_wildcard_re = re.compile(r"^\?\*\.")


def fix_leading_wildcard(s: str) -> str:
    return _leading_wildcard_re.sub("*.", s)


def _in_to_wildcard(tokens) -> str | None:
    """Convert an ``IN`` (character class) node to a wildcard class."""
    negate = tokens[0][0] == sre_parser.NEGATE
    content = ""
    for token_type, token_value in tokens[1:] if negate else tokens:
        if token_type == sre_parser.LITERAL:
            character = chr(token_value)
        elif token_type == sre_parser.RANGE:
            character = f"{chr(token_value[0])}-{chr(token_value[1])}"
        elif token_type == sre_parser.CATEGORY:
            # Only \d is used by the existing rules.
            character = "0-9" if token_value == sre_parser.CATEGORY_DIGIT else ""
        else:
            return None
        if not character or character in "[]\\":
            return None
        content += character
    if not content or (not negate and content[0] in "^!"):
        return None
    return f"[{'!' if negate else ''}{content}]"


def _ast_to_wildcard(parsed_pattern: sre_parser.SubPattern) -> list[str]:
    wildcards = [""]
    for token_type, token_value in parsed_pattern:
        if token_type in (sre_parser.MAX_REPEAT, sre_parser.MIN_REPEAT):
            min_repetitions, max_repetitions, sub_pattern = token_value
            if max_repetitions - min_repetitions > 5:
                # Unbounded or too wide to expand: the wildcard syntax can only
                # express "any string".
                wildcards = [wildcard + "*" for wildcard in wildcards]
            else:
                sub_wildcards = _ast_to_wildcard(sub_pattern)
                wildcards = [
                    wildcard_prefix + subpattern_wildcard * repetitions
                    for wildcard_prefix in wildcards
                    for subpattern_wildcard in sub_wildcards
                    for repetitions in range(min_repetitions, max_repetitions + 1)
                ]
        elif token_type == sre_parser.LITERAL:
            literal_character = chr(token_value)
            wildcards = [wildcard + literal_character for wildcard in wildcards]
        elif token_type == sre_parser.IN:
            character_class = _in_to_wildcard(token_value)
            if character_class is None:
                character_class = "?"
            wildcards = [wildcard + character_class for wildcard in wildcards]
        elif token_type == sre_parser.NOT_LITERAL:
            # A single negated literal is parsed as NOT_LITERAL, e.g. [^a].
            character = chr(token_value)
            if character in "[]\\":
                wildcards = [wildcard + "?" for wildcard in wildcards]
            else:
                wildcards = [wildcard + f"[!{character}]" for wildcard in wildcards]
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
