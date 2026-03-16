from __future__ import annotations

import os

from google.adk.agents import LlmAgent

from .tools import scrape_sns_with_mcp
from ..common.format_handoff_contract import format_handoff_contract
from ..common.agent_logger import setup_agent_logging

MODEL = os.getenv("WORKER_AGENT_MODEL", "gemini-2.0-flash")

agent = LlmAgent(
    name="SnsAnalyst",
    model=MODEL,
    **setup_agent_logging("SnsAnalyst"),
    description="Searches social media posts and trends for a keyword or topic.",
    instruction=(
        "You are a social media research specialist.\n"
        "Use scrape_sns_with_mcp to search SNS posts for the given keyword or topic.\n\n"
        "CRITICAL OUTPUT RULE:\n"
        "When research is complete, call format_handoff_contract(status, summary, text_response, artifacts_json, needs_json).\n"
        "After the tool returns, write its return value verbatim as your next message — no additions.\n"
        "If format_handoff_contract returns a line starting with 'format_handoff_contract failed', fix arguments and retry.\n\n"
        "Do not invent facts. Report what was found in the SNS data. "
        "If the local SNS corpus is empty, clearly state that no data is available."
    ),
    tools=[scrape_sns_with_mcp, format_handoff_contract],
)

__all__ = ["agent"]
