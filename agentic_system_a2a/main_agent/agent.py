from __future__ import annotations

import os

from google.adk.agents import LlmAgent

from .slack_tool import slack_post_message
from .sub_agent_tools import call_web_search_agent, call_paper_agent, call_sns_agent
from ..common.agent_logger import setup_agent_logging

MODEL = os.getenv("MAIN_AGENT_MODEL", "gemini-2.0-flash")

agent = LlmAgent(
    name="MainAgent",
    model=MODEL,
    **setup_agent_logging("MainAgent"),
    description="Orchestrates specialist agents to handle complex multi-step user requests.",
    instruction=(
        "You are the coordinator of a specialist agent team.\n\n"
        "Available tools:\n"
        "- call_web_search_agent(query): web search, current events, URLs, general knowledge\n"
        "- call_paper_agent(query): academic papers, research documents, DOI/arXiv lookup\n"
        "- call_sns_agent(keyword): social media posts, trends, public sentiment\n"
        "- slack_post_message(channel, text): send a message to a Slack channel\n\n"
        "Workflow:\n"
        "1. Understand the user request.\n"
        "2. Break it into steps if needed.\n"
        "3. Call the most appropriate agent(s) in sequence or in parallel reasoning.\n"
        "4. Synthesize the results into a clear, direct final answer.\n"
        "5. Cite sources and identifiers when available.\n\n"
        "Rules:\n"
        "- Do not make up facts. If an agent returns no useful result, say so.\n"
        "- Prefer calling agents over answering from memory for factual questions.\n"
        "- Keep the final answer concise and user-facing."
    ),
    tools=[call_web_search_agent, call_paper_agent, call_sns_agent, slack_post_message],
)

__all__ = ["agent"]
