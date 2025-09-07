from urllib.parse import urlparse, urlunparse

from pydantic import HttpUrl


def build_v2ray_include_url(base_url: HttpUrl, include: str) -> HttpUrl:
    """Build V2Ray include URL from base URL and include path."""
    parsed = urlparse(str(base_url))
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
