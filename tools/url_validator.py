from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """Return True when the URL has an HTTP(S) scheme and netloc."""
    if not isinstance(url, str) or not url.strip():
        return False

    parsed = urlparse(url.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
