"""
Intelligent URL Router (Step 2 & 3 Combined)
==============================================
Uses an LLM (via OpenAI compatible API) to classify URLs and assign agents.
Mutates records in-place.
"""

from __future__ import annotations

import logging
import json
from pydantic import BaseModel
from openai import OpenAI

logger = logging.getLogger(__name__)

# Constants as provided
GPT_API_KEY = "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"
GPT_BASE_URL = "https://integrate.api.nvidia.com/v1"
GPT_MODEL = "openai/gpt-oss-120b"

# Initialize client
client = OpenAI(
    api_key=GPT_API_KEY,
    base_url=GPT_BASE_URL,
)

class RoutingResult(BaseModel):
    platform: str
    type: str
    agent: str
    tool: str

SYSTEM_PROMPT = """
You are an intelligent URL routing assistant for a video asset pipeline.
Your job is to analyze a given URL and determine the standard platform, the content type,
and which agent and tool should be assigned to handle downloading the content.

Platform options mapping:
- "YouTube Public" URL -> platform: "YouTube_Public", agent: "youtube_agent", tool: "yt-dlp", type: "video"
- "YouTube Private" URL (has authentication query params like token, auth, key, si) -> platform: "YouTube_Private", agent: "youtube_agent", tool: "yt-dlp", type: "video"
- "Google Drive" URL (drive.google.com, docs.google.com) -> platform: "Google_Drive", agent: "drive_agent", tool: "gdown", type: "video"
- "Direct MP4" URL (ends with .mp4, .m3u8, .webm, .mkv, .avi, etc) -> platform: "Direct_MP4", agent: "direct_agent", tool: "requests", type: "video"
- "Vimeo" URL (vimeo.com) -> platform: "Vimeo", agent: "fallback_agent", tool: "requests", type: "video"
- Any other URL -> platform: "Unknown", agent: "fallback_agent", tool: "requests", type: "unknown"

You MUST output ONLY a valid JSON object matching the requested schema. No conversational text.
Example output format:
{
  "platform": "YouTube_Public",
  "type": "video",
  "agent": "youtube_agent",
  "tool": "yt-dlp"
}
"""

def route_urls(records: list[dict]) -> list[dict]:
    """
    Classify each record's URL and set ``platform``, ``type``, ``agent``, and ``tool`` **in-place**.
    Returns the same list for chaining convenience.
    """
    counters: dict[str, int] = {}

    for rec in records:
        url = rec.get("url", "")
        if not url:
            rec.update({
                "platform": "Unknown",
                "type": "unknown",
                "agent": "fallback_agent",
                "tool": "requests"
            })
            continue

        try:
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this URL and output JSON: {url}"}
                ],
                temperature=0.1,
                max_tokens=256
            )
            raw_content = response.choices[0].message.content.strip()
            
            # Simple cleanup in case model wrapped it in markdown
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            if raw_content.startswith("```"):
                raw_content = raw_content[3:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
            
            parsed = json.loads(raw_content)
            
            # Ensure valid defaults if model hallucinated
            platform = parsed.get("platform", "Unknown")
            content_type = parsed.get("type", "unknown")
            agent = parsed.get("agent", "fallback_agent")
            tool = parsed.get("tool", "requests")

        except Exception as e:
            logger.error("Error asking LLM for URL %s: %s", url, str(e))
            platform = "Unknown"
            content_type = "unknown"
            agent = "fallback_agent"
            tool = "requests"

        rec["platform"] = platform
        rec["type"] = content_type
        rec["agent"] = agent
        rec["tool"] = tool
        counters[platform] = counters.get(platform, 0) + 1

    logger.info(
        "Intelligent routing complete (%d URLs): %s",
        len(records),
        ", ".join(f"{k}: {v}" for k, v in sorted(counters.items())),
    )
    return records
