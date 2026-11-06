# Wildcard normalization is kept out of re_parser.py so that the file-level
# pyright suppression for the untyped re._parser API does not also cover this
# fully typed string logic.
import re

_star_re = re.compile(r"\*+")
_leading_wildcard_re = re.compile(r"^\?\*\.")


def normalize_wildcard(wildcard: str) -> str:
    collapsed = _star_re.sub("*", wildcard)
    return _leading_wildcard_re.sub("*.", collapsed)
