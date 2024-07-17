from config import LOGICAL_KEYWORDS, LOGICAL_AND_OR, LOGICAL_NOT


def is_logical_keyword(logical: str) -> bool:
    return logical.upper() in LOGICAL_KEYWORDS


def is_logical_and_or(logical: str) -> bool:
    return logical.upper() in LOGICAL_AND_OR


def is_logical_not(logical: str) -> bool:
    return logical.upper() == LOGICAL_NOT
