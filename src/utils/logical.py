# Logical rule constants
LOGICAL_KEYWORDS = ["AND", "OR", "NOT"]
LOGICAL_AND_OR = ["AND", "OR"]
LOGICAL_NOT = "NOT"


def is_logical_keyword(logical: str) -> bool:
    """Check if string is a logical keyword."""
    return logical.upper() in LOGICAL_KEYWORDS


def is_logical_and_or(logical: str) -> bool:
    """Check if string is AND or OR logical operator."""
    return logical.upper() in LOGICAL_AND_OR


def is_logical_not(logical: str) -> bool:
    """Check if string is NOT logical operator."""
    return logical.upper() == LOGICAL_NOT
