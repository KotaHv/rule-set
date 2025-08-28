import hashlib
from typing import Any


def generate_cache_key(key: Any) -> str:
    """Generate SHA256 hash for cache key."""
    return hashlib.sha256(str(key).encode()).hexdigest()
