"""
IAVARS — LLM Configuration
===========================
Centralises all LLM provider settings and environment-variable loading.

The agent uses OpenAI by default.  To switch providers (Anthropic, Groq, etc.)
change `get_llm()` — everything else stays the same.

Environment variables (set in .env or OS environment):
    OPENAI_API_KEY       — required for OpenAI models
    LLM_MODEL            — override model name (default: gpt-4o-mini)
    LLM_TEMPERATURE      — 0.0–1.0 (default: 0 for deterministic output)
    MAX_AGENT_ITERATIONS — safety cap on agent reasoning loops (default: 15)
"""

import os
from dotenv import load_dotenv

# Load .env file from any parent directory that has one
load_dotenv()

# ─── Resolved settings ───────────────────────────────────────────────────────

LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))
MAX_ITERATIONS: int = int(os.getenv("MAX_AGENT_ITERATIONS", "15"))


# ─── LLM factory ─────────────────────────────────────────────────────────────

def get_llm(model: str = LLM_MODEL, temperature: float = LLM_TEMPERATURE):
    """
    Return a configured ChatOpenAI instance.

    Raises:
        EnvironmentError: If OPENAI_API_KEY is not set.
    """
    from langchain_openai import ChatOpenAI  # imported lazily to avoid hard dep at import time

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set.  "
            "Add it to a .env file or export it as an environment variable."
        )

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        # Streaming kept off so tool-calling JSON is returned atomically
        streaming=False,
    )
