from __future__ import annotations

import os

from google.adk.agents import LlmAgent

from .tools import search_web_with_mcp
from ..common.format_handoff_contract import format_handoff_contract
from ..common.agent_logger import setup_agent_logging

MODEL = os.getenv("WORKER_AGENT_MODEL", "gemini-2.0-flash")

agent = LlmAgent(
    name="WebSearchAnalyst",
    model=MODEL,
    **setup_agent_logging("WebSearchAnalyst"),
    description="Searches the web and returns structured research results.",
    instruction=(
        "You are a web research specialist.\n"
        "Use search_web_with_mcp to find relevant information.\n\n"
        "CRITICAL OUTPUT RULE:\n"
        "When research is complete, call format_handoff_contract(status, summary, text_response, artifacts_json, needs_json).\n"
        "After the tool returns, write its return value verbatim as your next message — no additions.\n"
        "If format_handoff_contract returns a line starting with 'format_handoff_contract failed', fix arguments and retry.\n\n"
        "Do not invent facts. If evidence is weak, say so clearly."
    ),
    tools=[search_web_with_mcp, format_handoff_contract],
)

__all__ = ["agent"]
