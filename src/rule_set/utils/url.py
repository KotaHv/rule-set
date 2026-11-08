from pathlib import Path
from urllib.parse import urlparse, urlunparse

from pydantic import HttpUrl


def build_v2ray_include_url(base: HttpUrl | Path, include: str) -> HttpUrl | Path:
    """Build V2Ray include source from base source and include path."""
    if isinstance(base, Path):
        return base.parent / include

    parsed = urlparse(str(base))
    new_path = parsed.path.rsplit("/", 1)[0] + f"/{include}"

    new_url = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            new_path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )
    return HttpUrl(new_url)
