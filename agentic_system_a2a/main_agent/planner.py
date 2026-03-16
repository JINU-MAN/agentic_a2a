from __future__ import annotations

import json

from google.adk.tools.tool_context import ToolContext

from .sub_agent_tools import call_web_search_agent, call_paper_agent, call_sns_agent
from .slack_tool import slack_post_message

_STATE_KEY = "agentic_plan"
_VALID_AGENTS = {"web_search", "paper", "sns", "slack"}


def create_plan(goal: str, steps_json: str, tool_context: ToolContext) -> str:
    """
    Create or replan the execution plan.

    Call this before execute_plan_step, or to replan mid-execution.
    On replan, completed steps and their results are automatically preserved.

    Args:
        goal: The overall goal or user request.
        steps_json: JSON array of remaining steps to execute.
            Each step must have:
              - "description": str — what this step does
              - "agent": "web_search" | "paper" | "sns" | "slack"
              - "query": str — query or message to pass to the agent
                         For slack, use "channel::message" format.
            Example:
              '[{"description":"Search web","agent":"web_search","query":"AI trends 2025"},
                {"description":"Post to slack","agent":"slack","query":"general::Results: ..."}]'

    Returns:
        Plan summary. Call execute_plan_step to start execution.
    """
    try:
        new_steps_raw = json.loads(steps_json)
    except json.JSONDecodeError as e:
        return f"create_plan failed: invalid steps_json — {e}"

    if not isinstance(new_steps_raw, list) or not new_steps_raw:
        return "create_plan failed: steps_json must be a non-empty JSON array"

    # Preserve completed steps from existing plan (replan context)
    existing = tool_context.state.get(_STATE_KEY) or {}
    completed = [s for s in existing.get("steps", []) if s.get("status") == "done"]

    new_steps = []
    for i, raw in enumerate(new_steps_raw):
        if not isinstance(raw, dict):
            return f"create_plan failed: step[{i}] must be an object"
        agent = str(raw.get("agent", "")).strip()
        if agent not in _VALID_AGENTS:
            return (
                f'create_plan failed: step[{i}].agent "{agent}" is invalid'
                f" — must be one of: {', '.join(sorted(_VALID_AGENTS))}"
            )
        query = str(raw.get("query", "")).strip()
        if not query:
            return f"create_plan failed: step[{i}].query must not be empty"
        new_steps.append({
            "id": len(completed) + i,
            "description": str(raw.get("description", query)).strip(),
            "agent": agent,
            "query": query,
            "status": "pending",
            "result_summary": "",
        })

    plan = {
        "goal": goal,
        "steps": completed + new_steps,
        "current_step": len(completed),
    }
    tool_context.state[_STATE_KEY] = plan

    lines = [f"Plan ready — goal: {goal}"]
    if completed:
        lines.append(f"  (Replan: {len(completed)} completed step(s) preserved)")
    for s in plan["steps"]:
        marker = "✓" if s["status"] == "done" else "→"
        lines.append(f"  {marker} [{s['id']}] {s['description']}  (agent: {s['agent']})")
    lines.append(f"\nCall execute_plan_step to start from step {plan['current_step']}.")
    return "\n".join(lines)


def execute_plan_step(tool_context: ToolContext) -> str:
    """
    Execute the next pending step in the current plan.

    Call repeatedly until all steps are done.
    Each call returns the step result plus:
      - a summary of all completed steps (for replan context)
      - the remaining step list

    If the result suggests the remaining steps need adjustment,
    call create_plan again — completed steps are preserved automatically.

    Returns:
        Step result with context summary and remaining steps.
    """
    plan = tool_context.state.get(_STATE_KEY)
    if not plan:
        return "No plan found. Call create_plan first."

    steps = plan.get("steps", [])
    current_idx = plan.get("current_step", 0)

    if current_idx >= len(steps):
        return "All steps completed. Synthesize the results and provide the final answer."

    step = steps[current_idx]
    agent = step["agent"]
    query = step["query"]

    try:
        if agent == "web_search":
            result = call_web_search_agent(query)
        elif agent == "paper":
            result = call_paper_agent(query)
        elif agent == "sns":
            result = call_sns_agent(query)
        elif agent == "slack":
            if "::" in query:
                channel, message = query.split("::", 1)
            else:
                channel, message = "general", query
            result = slack_post_message(channel.strip(), message.strip())
        else:
            result = f"Unknown agent: {agent}"
    except Exception as exc:
        result = f"Step execution failed: {exc}"

    step["status"] = "done"
    step["result_summary"] = result[:400]
    plan["current_step"] = current_idx + 1
    tool_context.state[_STATE_KEY] = plan

    done = [s for s in steps if s["status"] == "done"]
    pending = [s for s in steps if s["status"] == "pending"]

    lines = [f"Step [{step['id']}] done — {step['description']}", "", "Result:", result]

    if done:
        lines += ["", "── Completed steps ──"]
        for s in done:
            lines.append(f"  [{s['id']}] {s['description']}: {s['result_summary'][:200]}")

    if pending:
        lines += ["", f"── Remaining ({len(pending)}) ──"]
        for s in pending:
            lines.append(f"  [{s['id']}] {s['description']}  (agent: {s['agent']})")
        lines.append("\nCall execute_plan_step to continue, or create_plan to replan.")
    else:
        lines.append("\nAll steps completed. Synthesize the results and provide the final answer.")

    return "\n".join(lines)


__all__ = ["create_plan", "execute_plan_step"]
