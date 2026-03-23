"""
IAVARS — Utility Helpers
=========================
Shared utility functions used across the agent, services, and UI layers.

All I/O-affecting utilities (folder creation, file writing) are idempotent and
safe to call multiple times.
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

# ─── Logger ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)-8s]  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("IAVARS")


# ─── Folder Constants ─────────────────────────────────────────────────────────

# Canonical mapping: platform name → relative download sub-folder
PLATFORM_FOLDERS: Dict[str, str] = {
    "youtube":      "downloads/youtube",
    "google_drive": "downloads/google_drive",
    "vimeo":        "downloads/vimeo",
    "dropbox":      "downloads/dropbox",
    "direct_files": "downloads/direct_files",
    "unknown":      "downloads/unknown",
}


# ─── Folder Utilities ─────────────────────────────────────────────────────────

def create_download_folders(base_dir: str = ".") -> Dict[str, str]:
    """
    Create the standard platform-based download folder tree.

    Args:
        base_dir: Root directory under which `downloads/` is created.

    Returns:
        Dict mapping platform name → absolute folder path.

    Example output:
        {
            "youtube":      "/project/downloads/youtube",
            "google_drive": "/project/downloads/google_drive",
            ...
        }
    """
    folders: Dict[str, str] = {}
    for platform, rel_path in PLATFORM_FOLDERS.items():
        full_path = os.path.join(base_dir, rel_path)
        os.makedirs(full_path, exist_ok=True)
        folders[platform] = os.path.abspath(full_path)
        logger.debug("Folder ready: %s", full_path)

    # Also create reports dir
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    logger.info("Download folder tree created under '%s'", os.path.abspath(base_dir))
    return folders


# ─── File Name Utilities ──────────────────────────────────────────────────────

_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """
    Replace filesystem-unsafe characters and trim to a safe length.

    Args:
        name:       Raw filename (may contain special characters).
        max_length: Maximum character length after sanitisation (default 200).

    Returns:
        A filesystem-safe filename string.
    """
    sanitized = _INVALID_CHARS.sub("_", name).strip(". ")
    return sanitized[:max_length] or "video"


def unique_filename(folder: str, filename: str) -> str:
    """
    Return a non-colliding filename by appending a counter if needed.

    Args:
        folder:   Target directory.
        filename: Desired filename (including extension).

    Returns:
        Path string guaranteed not to already exist.
    """
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(folder, filename)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(folder, f"{base}_{counter}{ext}")
        counter += 1
    return candidate


# ─── Report Utilities ─────────────────────────────────────────────────────────

def save_json_report(report: Dict[str, Any], output_path: str) -> str:
    """
    Serialise *report* to a pretty-printed JSON file.

    Args:
        report:      Dict to serialise.
        output_path: Destination file path (parent directories created if absent).

    Returns:
        Absolute path of the saved file.
    """
    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str, ensure_ascii=False)

    abs_path = os.path.abspath(output_path)
    logger.info("Report saved → %s", abs_path)
    return abs_path


def load_json_report(path: str) -> Dict[str, Any]:
    """Load a JSON report from disk."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ─── Misc Utilities ───────────────────────────────────────────────────────────

def timestamp_suffix() -> str:
    """Return a compact timestamp string suitable for file names."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def flatten_list(nested: List[Any]) -> List[Any]:
    """Flatten one level of nesting in a list."""
    result: List[Any] = []
    for item in nested:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result


def url_to_filename(url: str, extension: str = ".mp4") -> str:
    """
    Derive a safe filename from a URL.

    Takes the last path segment of the URL, sanitises it, and appends
    *extension* if the segment has no recognised video extension.

    Args:
        url:       Source URL string.
        extension: Fallback extension (default ".mp4").

    Returns:
        A sanitised filename string.
    """
    segment = url.rstrip("/").split("/")[-1].split("?")[0] or "video"
    name = sanitize_filename(segment, max_length=100)
    known_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v"}
    if not any(name.lower().endswith(ext) for ext in known_exts):
        name += extension
    return name
