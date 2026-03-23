"""
IAVARS — Platform Detector
===========================
Detects the video-hosting platform of any URL using regex pattern matching.

Platforms recognised:
  youtube       — YouTube watch / short / embed links and youtu.be short URLs
  google_drive  — Google Drive and Docs share links
  vimeo         — Vimeo player and standard video pages
  dropbox       — Dropbox shared links and direct CDN links
  direct_files  — Any URL that ends with a common video file extension
  unknown       — Anything that does not match the above

Usage:
    from services.platform_detector import detect_platform, group_by_platform

    platform = detect_platform("https://youtu.be/dQw4w9WgXcQ")
    # → "youtube"

    groups = group_by_platform(["https://youtu.be/abc", "https://vimeo.com/123"])
    # → {"youtube": ["https://youtu.be/abc"], "vimeo": ["https://vimeo.com/123"]}
"""

import re
from typing import Dict, List

# ─── Pattern Registry ────────────────────────────────────────────────────────
# Each key is the canonical platform name used throughout the project.
# Patterns are tested in declaration order; first match wins.

PLATFORM_PATTERNS: Dict[str, List[str]] = {
    "youtube": [
        r"(?:https?://)?(?:www\.)?youtube\.com/watch\?.*v=[\w-]+",
        r"(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+",
        r"(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+",
        r"(?:https?://)?(?:www\.)?youtube\.com/live/[\w-]+",
        r"(?:https?://)?youtu\.be/[\w-]+",
    ],
    "google_drive": [
        r"(?:https?://)?drive\.google\.com/",
        r"(?:https?://)?docs\.google\.com/",
    ],
    "vimeo": [
        r"(?:https?://)?(?:www\.)?vimeo\.com/\d+",
        r"(?:https?://)?player\.vimeo\.com/video/\d+",
    ],
    "dropbox": [
        r"(?:https?://)?(?:www\.)?dropbox\.com/s/",
        r"(?:https?://)?(?:www\.)?dropbox\.com/scl/",
        r"(?:https?://)?dl\.dropboxusercontent\.com/",
    ],
    # Direct video file links — checked last so platform-hosted links match first
    "direct_files": [
        r"\.mp4(?:[?#]|$)",
        r"\.mov(?:[?#]|$)",
        r"\.avi(?:[?#]|$)",
        r"\.mkv(?:[?#]|$)",
        r"\.webm(?:[?#]|$)",
        r"\.flv(?:[?#]|$)",
        r"\.wmv(?:[?#]|$)",
        r"\.m4v(?:[?#]|$)",
    ],
}


# ─── Public API ───────────────────────────────────────────────────────────────

def detect_platform(url: str) -> str:
    """
    Return the platform name for a single URL.

    Args:
        url: The URL string to classify.

    Returns:
        One of: "youtube", "google_drive", "vimeo", "dropbox",
                "direct_files", or "unknown".
    """
    url = (url or "").strip()
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return platform
    return "unknown"


def detect_platforms_bulk(urls: List[str]) -> Dict[str, str]:
    """
    Classify a list of URLs, returning a {url: platform} mapping.

    Args:
        urls: List of URL strings.

    Returns:
        Dict mapping each URL to its detected platform name.
    """
    return {url: detect_platform(url) for url in urls}


def group_by_platform(urls: List[str]) -> Dict[str, List[str]]:
    """
    Group a list of URLs by detected platform.

    Args:
        urls: List of URL strings.

    Returns:
        Dict mapping platform name → list of matching URLs.
    """
    groups: Dict[str, List[str]] = {}
    for url in urls:
        platform = detect_platform(url)
        groups.setdefault(platform, []).append(url)
    return groups
