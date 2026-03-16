from __future__ import annotations

import os

from google.adk.agents import LlmAgent

from .tools import (
    scrape_papers_with_mcp,
    fetch_external_paper_with_mcp,
    load_paper_memory_with_mcp,
    expand_paper_memory_with_mcp,
    query_paper_memory,
)
from ..common.format_handoff_contract import format_handoff_contract
from ..common.agent_logger import setup_agent_logging

MODEL = os.getenv("WORKER_AGENT_MODEL", "gemini-2.0-flash")

agent = LlmAgent(
    name="PaperAnalyst",
    model=MODEL,
    **setup_agent_logging("PaperAnalyst"),
    description="Searches academic papers and research documents in the local corpus or by DOI/arXiv ID.",
    instruction=(
        "You are a paper research specialist. "
        "Own paper-specific retrieval from the local corpus, workflow-scoped paper memory, and external paper identifiers. "
        "Inspect workflow artifacts before starting a fresh search, prefer the lightest evidence path that can answer the question, "
        "and state clearly when the result relies only on metadata or partial context.\n\n"
        "Your direct tools return JSON with `ok`, `tool_name`, `summary`, `content_type`, `items`, `data`, `errors`, and `metadata`; "
        "read those fields internally and do not echo raw tool output as the final workflow answer.\n\n"
        "CRITICAL OUTPUT RULE:\n"
        "When your research is complete, call format_handoff_contract(status, summary, text_response, artifacts_json, needs_json).\n"
        "After the tool returns, write its return value verbatim as your next message — copy the returned string exactly as a text message with no additions.\n"
        "If format_handoff_contract returns a line starting with 'format_handoff_contract failed', fix the arguments and call it again before writing anything.\n\n"
        "Cite the most relevant papers, explain why they matter, and do not invent facts. "
        "If the local corpus is insufficient, clearly say so and state what is needed next."
    ),
    tools=[
        scrape_papers_with_mcp,
        fetch_external_paper_with_mcp,
        load_paper_memory_with_mcp,
        expand_paper_memory_with_mcp,
        query_paper_memory,
        format_handoff_contract,
    ],
)

__all__ = ["agent"]
