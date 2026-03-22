from __future__ import annotations

import json
import os
import re
from typing import Dict


DEFAULT_INTENT = {"group_by": "none", "filter": "none"}

# Simple local brand hints used when remote model inference is unavailable.
BRAND_HINTS = {
    "nike": "nike",
    "adidas": "adidas",
    "puma": "puma",
    "reebok": "reebok",
    "underarmour": "underarmour",
    "under armour": "underarmour",
    "ua": "underarmour",
}


def _normalize_intent(payload: dict) -> Dict[str, str]:
    group_by = str(payload.get("group_by", "none")).strip().lower()
    filter_value = str(payload.get("filter", "none")).strip().lower()

    if group_by not in {"none", "brand", "campaign"}:
        group_by = "none"
    if not filter_value:
        filter_value = "none"

    return {"group_by": group_by, "filter": filter_value}


def _extract_json_object(text: str) -> dict | None:
    if not text:
        return None

    raw_text = text.strip()
    if not raw_text:
        return None

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def _local_intent_fallback(text: str) -> Dict[str, str]:
    lowered = (text or "").strip().lower()
    intent = DEFAULT_INTENT.copy()

    if not lowered:
        return intent

    if "group by brand" in lowered:
        intent["group_by"] = "brand"
    elif "group by campaign" in lowered:
        intent["group_by"] = "campaign"

    for hint, canonical in BRAND_HINTS.items():
        if hint in lowered:
            intent["filter"] = canonical
            break

    return intent


def analyse_instruction(text: str, model_name: str = "models/gemini-1.5-flash") -> Dict[str, str]:
    fallback_intent = _local_intent_fallback(text)

    if not (text or "").strip():
        return fallback_intent

    try:
        from dotenv import load_dotenv
        import google.generativeai as genai
    except ImportError:
        return fallback_intent

    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        return fallback_intent

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    prompt = f"""
    You are an AI agent.
    Extract structured intent from the user instruction below.

    Instruction:
    {text}

    Return ONLY valid JSON with this shape:
    {{
        "group_by": "none|brand|campaign",
        "filter": "none|<brand>"
    }}
    """

    try:
        response = model.generate_content(prompt, request_options={"timeout": 8})
    except TypeError:
        # Older SDKs may not support request_options on this call signature.
        try:
            response = model.generate_content(prompt)
        except Exception:
            return fallback_intent
    except Exception:
        return fallback_intent

    response_payload = _extract_json_object(getattr(response, "text", ""))
    if not isinstance(response_payload, dict):
        return fallback_intent

    return _normalize_intent(response_payload)
