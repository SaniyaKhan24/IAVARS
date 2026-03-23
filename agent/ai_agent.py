"""
IAVARS — AI Agent Controller
==============================
This module builds, configures, and exposes the LangChain tool-calling agent
that orchestrates the entire video-retrieval workflow.

Architecture
────────────
  ┌──────────────────────────────────────────────────────────────────────┐
  │  User instruction + spreadsheet path                                 │
  │                         │                                            │
  │              ┌──────────▼───────────┐                               │
  │              │   IVARSAgent.run()   │                               │
  │              └──────────┬───────────┘                               │
  │                         │                                            │
  │          ┌──────────────▼───────────────────┐                       │
  │          │   LangChain AgentExecutor         │                       │
  │          │   (tool-calling / ReAct loop)     │                       │
  │          │                                   │                       │
  │          │  LLM (ChatOpenAI / gpt-4o-mini)   │                       │
  │          │      ↕ tool calls ↕               │                       │
  │          │  parse_spreadsheet                │                       │
  │          │  extract_urls                     │                       │
  │          │  detect_platforms                 │                       │
  │          │  filter_urls                      │                       │
  │          │  create_download_folders_tool     │                       │
  │          │  download_videos                  │                       │
  │          │  organize_files                   │                       │
  │          │  generate_report                  │                       │
  │          └───────────────────────────────────┘                       │
  │                         │                                            │
  │              ┌──────────▼───────────┐                               │
  │              │  Structured result   │                               │
  │              │  {action_plan, ...}  │                               │
  │              └──────────────────────┘                               │
  └──────────────────────────────────────────────────────────────────────┘
"""

import json
import sys
import os
from typing import List, Optional

# Ensure project root is on sys.path when this module is run directly
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent.prompts import SYSTEM_PROMPT
from agent.tools import ALL_TOOLS
from config.llm_config import get_llm, MAX_ITERATIONS
from utils.helpers import logger


# ─── Agent Builder ────────────────────────────────────────────────────────────

def build_agent_executor() -> AgentExecutor:
    """
    Instantiate and return a ready-to-use LangChain AgentExecutor.

    The executor wraps a tool-calling agent that binds the LLM to the full
    IAVARS tool set.  verbose=True prints the reasoning trace to stdout,
    which is useful during development; set it to False in production.
    """
    llm = get_llm()

    # Prompt layout expected by create_tool_calling_agent:
    #   system → (optional) chat_history → human turn → agent_scratchpad
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm=llm, tools=ALL_TOOLS, prompt=prompt)

    executor = AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        verbose=True,                # set False to suppress trace output
        max_iterations=MAX_ITERATIONS,
        handle_parsing_errors=True,  # gracefully recover from LLM format glitches
        return_intermediate_steps=True,
    )

    logger.info("AgentExecutor built with %d tools", len(ALL_TOOLS))
    return executor


# ─── High-Level Agent Class ───────────────────────────────────────────────────

class IVARSAgent:
    """
    High-level interface for the IAVARS AI agent.

    Usage:
        agent = IVARSAgent()
        result = agent.run(
            user_instruction="Download only advertisement videos",
            spreadsheet_path="/path/to/links.xlsx",
        )
        print(result["summary"])
    """

    def __init__(self) -> None:
        self._executor: AgentExecutor = build_agent_executor()
        logger.info("IVARSAgent ready.")

    # ── Public method ─────────────────────────────────────────────────────────

    def run(
        self,
        user_instruction: str,
        spreadsheet_path: str,
        output_dir: str = ".",
        chat_history: Optional[List[BaseMessage]] = None,
    ) -> dict:
        """
        Execute the complete IAVARS workflow.

        Args:
            user_instruction: Natural language command from the user.
            spreadsheet_path: Path to the Excel / CSV file to process.
            output_dir:       Where to create download folders and reports.
            chat_history:     Prior conversation messages for multi-turn context.

        Returns:
            Structured result dict matching the schema:
            {
                "action_plan":     [...],
                "platform_groups": {...},
                "download_status": {...},
                "summary":         {...},
                "errors":          [...],
            }
        """
        logger.info("IVARSAgent.run | instruction='%s'", user_instruction)
        logger.info("IVARSAgent.run | spreadsheet='%s'", spreadsheet_path)

        # Build a fully-specified prompt so the agent has all context up-front
        full_input = (
            f"User instruction : {user_instruction}\n"
            f"Spreadsheet path : {spreadsheet_path}\n"
            f"Output directory : {output_dir}\n\n"
            "Execute the complete IAVARS workflow:\n"
            "  1. Call parse_spreadsheet with the spreadsheet path above.\n"
            "  2. Call extract_urls on the result.\n"
            "  3. Call detect_platforms on the URL list.\n"
            "  4. Call filter_urls using the user instruction as the filter.\n"
            "  5. Call create_download_folders_tool with the output directory.\n"
            "  6. Call download_videos with the filtered URLs and output directory.\n"
            "  7. Call organize_files using the strategy implied by the instruction.\n"
            "  8. Call generate_report to produce the final JSON report.\n\n"
            "Return the report JSON as your final answer."
        )

        try:
            raw = self._executor.invoke({
                "input": full_input,
                "chat_history": chat_history or [],
            })
            return self._parse_output(raw)

        except Exception as exc:
            logger.error("IVARSAgent.run failed: %s", exc, exc_info=True)
            return {
                "action_plan": [],
                "platform_groups": {},
                "download_status": {},
                "summary": {"total_urls": 0, "succeeded": 0, "failed": 0},
                "errors": [str(exc)],
            }

    # ── Output Normaliser ─────────────────────────────────────────────────────

    def _parse_output(self, raw: dict) -> dict:
        """
        Extract and normalise the structured result from the agent's raw output.

        The agent's final answer may be:
          a) A JSON string embedded in the 'output' field  → parse directly.
          b) Plain text                                    → reconstruct from steps.
        """
        output_text: str = raw.get("output", "")
        intermediate: list = raw.get("intermediate_steps", [])

        # Attempt to parse JSON block from the final output
        try:
            start = output_text.find("{")
            end = output_text.rfind("}") + 1
            if start != -1 and end > start:
                parsed = json.loads(output_text[start:end])
                # Ensure mandatory keys are present
                parsed.setdefault("action_plan", [])
                parsed.setdefault("platform_groups", {})
                parsed.setdefault("download_status", {})
                parsed.setdefault("errors", [])
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: reconstruct a minimal result from intermediate tool steps
        logger.warning("Could not parse JSON from agent output; reconstructing from steps.")
        action_plan = []
        for step in intermediate:
            tool_call = step[0]  # AgentAction
            action_plan.append(f"{tool_call.tool}({tool_call.tool_input})")

        return {
            "action_plan": action_plan,
            "platform_groups": {},
            "download_status": {},
            "summary": {"total_urls": 0, "succeeded": 0, "failed": 0},
            "errors": [],
            "raw_output": output_text,
        }


# ─── CLI Entry-point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the IAVARS agent from the command line.")
    parser.add_argument("spreadsheet", help="Path to the Excel or CSV spreadsheet")
    parser.add_argument(
        "--instruction",
        default="Download all videos and organise them by platform",
        help="Natural language instruction",
    )
    parser.add_argument("--output-dir", default=".", help="Output directory for downloads and reports")
    args = parser.parse_args()

    agent = IVARSAgent()
    result = agent.run(
        user_instruction=args.instruction,
        spreadsheet_path=args.spreadsheet,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, indent=2))
