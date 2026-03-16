from __future__ import annotations

import os

from google.adk.agents import LlmAgent

from .slack_tool import slack_post_message
from .sub_agent_tools import call_web_search_agent, call_paper_agent, call_sns_agent
from .planner import create_plan, execute_plan_step
from ..common.agent_logger import setup_agent_logging

MODEL = os.getenv("MAIN_AGENT_MODEL", "gemini-2.0-flash")

agent = LlmAgent(
    name="MainAgent",
    model=MODEL,
    **setup_agent_logging("MainAgent"),
    description="Orchestrates specialist agents to handle complex multi-step user requests.",
    instruction=(
        "You are the coordinator of a specialist agent team.\n\n"

        "## Direct tools (simple single-step requests)\n"
        "- call_web_search_agent(query): web search, current events, URLs, general knowledge\n"
        "- call_paper_agent(query): academic papers, research documents, DOI/arXiv lookup\n"
        "- call_sns_agent(keyword): social media posts, trends, public sentiment\n"
        "- slack_post_message(channel, text): send a message to a Slack channel\n\n"

        "## Planner tools (multi-step requests)\n"
        "Use these when the request requires multiple sequential operations.\n"
        "- create_plan(goal, steps_json): define the execution plan\n"
        "- execute_plan_step(): execute the next step; returns result + completed context + remaining steps\n\n"

        "### Planning workflow\n"
        "1. Call create_plan with the goal and all steps as a JSON array.\n"
        "   Each step: {\"description\": str, \"agent\": \"web_search\"|\"paper\"|\"sns\"|\"slack\", \"query\": str}\n"
        "   For slack steps, query format: \"channel::message\"\n"
        "2. Call execute_plan_step repeatedly — one call per step.\n"
        "3. After each step, review the result.\n"
        "   - If the remaining steps are still appropriate: continue with execute_plan_step.\n"
        "   - If the result changes what needs to be done next: call create_plan again with updated steps.\n"
        "     Completed steps and their results are preserved automatically — only pass the new remaining steps.\n"
        "4. When all steps are done, synthesize the results into a final answer.\n\n"

        "## Rules\n"
        "- Do not make up facts. If an agent returns no useful result, say so.\n"
        "- Prefer calling agents over answering from memory for factual questions.\n"
        "- Keep the final answer concise and user-facing."
    ),
    tools=[
        call_web_search_agent, call_paper_agent, call_sns_agent, slack_post_message,
        create_plan, execute_plan_step,
    ],
)

__all__ = ["agent"]
