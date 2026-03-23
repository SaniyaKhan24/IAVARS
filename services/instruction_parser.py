"""
IAVARS — Instruction Parser
============================
Converts a free-form natural language instruction into a structured command
dict that the agent and filter tool can act on directly.

The parser uses keyword matching so it works without an LLM call, keeping
latency low and making it easy to unit-test.

Parsed output schema:
    {
        "action":      "download" | "organize" | "validate" | "report",
        "filter":      "all" | "<platform>" | "<content-type keyword>",
        "organize_by": "platform" | "brand" | "type",
        "raw_instruction": "<original text>"
    }

Examples:
    parse_instruction("Download all videos")
    → {"action": "download", "filter": "all", "organize_by": "platform", ...}

    parse_instruction("Download only advertisement videos")
    → {"action": "download", "filter": "advertisement", "organize_by": "platform", ...}

    parse_instruction("Organize videos platform-wise")
    → {"action": "organize", "filter": "all", "organize_by": "platform", ...}

    parse_instruction("Download videos and group them by brand")
    → {"action": "download", "filter": "all", "organize_by": "brand", ...}
"""

from typing import Dict

# ─── Keyword Maps ─────────────────────────────────────────────────────────────

# Maps canonical action names → trigger words (all lower-case)
_ACTION_KEYWORDS: Dict[str, list] = {
    "download":  ["download", "fetch", "get", "retrieve", "pull", "save"],
    "organize":  ["organise", "organize", "sort", "group", "arrange", "categorise", "categorize"],
    "validate":  ["validate", "check", "verify", "test", "inspect"],
    "report":    ["report", "summarise", "summarize", "list", "show", "display"],
}

# Maps canonical filter names → trigger words
# Platform names must match PLATFORM_PATTERNS keys in platform_detector.py
_FILTER_KEYWORDS: Dict[str, list] = {
    "youtube":      ["youtube", "yt"],
    "google_drive": ["google drive", "drive", "gdrive"],
    "vimeo":        ["vimeo"],
    "dropbox":      ["dropbox"],
    "direct_files": ["direct", "direct file", "mp4", "mov", "raw"],
    "advertisement": ["advertisement", "ad", "ads", "advert", "promo", "promotional", "commercial"],
    "brand":        ["brand", "company", "corporate", "client"],
    # "all" is the default — no trigger needed
}

# Maps canonical organization strategies → trigger words
_ORGANIZE_KEYWORDS: Dict[str, list] = {
    "platform": ["platform", "platform-wise", "by platform", "source", "by source", "site"],
    "brand":    ["brand", "brand-wise", "by brand", "company", "by company", "client"],
    "type":     ["type", "type-wise", "by type", "category", "by category", "format"],
}


# ─── Public API ───────────────────────────────────────────────────────────────

def parse_instruction(instruction: str) -> Dict[str, str]:
    """
    Parse a natural language instruction into a structured command.

    Args:
        instruction: Free-form user instruction string.

    Returns:
        Dict with keys: action, filter, organize_by, raw_instruction.
    """
    text = instruction.lower().strip()

    action = _match_first(text, _ACTION_KEYWORDS, default="download")
    filter_type = _match_first(text, _FILTER_KEYWORDS, default="all")
    organize_by = _match_first(text, _ORGANIZE_KEYWORDS, default="platform")

    return {
        "action": action,
        "filter": filter_type,
        "organize_by": organize_by,
        "raw_instruction": instruction,
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _match_first(text: str, keyword_map: Dict[str, list], default: str) -> str:
    """
    Return the first canonical key whose trigger phrase appears in *text*.
    Falls back to *default* if nothing matches.
    """
    for canonical, triggers in keyword_map.items():
        for trigger in triggers:
            # Use word-boundary-aware search for short triggers (e.g. "ad")
            if trigger in text:
                return canonical
    return default
