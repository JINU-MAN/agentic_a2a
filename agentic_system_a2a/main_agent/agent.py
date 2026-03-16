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

        "## Planner tools (multi-step requests only)\n"
        "Use ONLY when ALL of these are true:\n"
        "  - 3 or more agent calls are needed\n"
        "  - the order of steps matters (later steps depend on earlier results)\n"
        "  - a single agent call cannot satisfy the request alone\n"
        "For anything else, use direct tools above.\n\n"
        "- create_plan(goal, steps_json): define the execution plan (max 6 steps total)\n"
        "- execute_plan_step(): execute the next step\n\n"

        "### Planning workflow\n"
        "1. Call create_plan with the goal and steps as a JSON array.\n"
        "   Each step: {\"description\": str, \"agent\": \"web_search\"|\"paper\"|\"sns\"|\"slack\", \"query\": str}\n"
        "   For slack steps, query format: \"channel::message\"\n"
        "   Keep the number of steps to the minimum necessary.\n"
        "2. Call execute_plan_step repeatedly — one call per step.\n"
        "3. Replan only if a step fails or returns results that make the remaining steps clearly wrong.\n"
        "   Do not replan just because a result is partial or imperfect.\n"
        "   On replan, pass only the new remaining steps — completed steps are preserved automatically.\n"
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
