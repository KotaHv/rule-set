import hashlib


def generate_cache_key(key: str) -> str:
    """Generate SHA256 hash for cache key."""
    return hashlib.sha256(key.encode()).hexdigest()
