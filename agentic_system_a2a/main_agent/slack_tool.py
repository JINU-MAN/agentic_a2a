from __future__ import annotations

import logging
import os
from pathlib import Path

from ..common.mcp_client import call_mcp_tool
from ..common.tool_output_utils import render_tool_output


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]


def _resolve_slack_server_path() -> str:
    # Resolve at call time so .env values loaded after import are reflected.
    explicit = str(os.getenv("SLACK_MCP_SERVER_PATH", "")).strip()
    if explicit:
        return explicit
    return str(BASE_DIR / "mcp_local" / "slack_server.py")


def slack_post_message(channel: str, text: str) -> str:
    """
    Post a message to a Slack channel.
    Use this when the user asks to send, notify, or share results on Slack.
    Returns a confirmation with the channel name and message timestamp.
    """
    slack_server_path = _resolve_slack_server_path()

    if not slack_server_path:
        msg = "SLACK_MCP_SERVER_PATH is not configured."
        return render_tool_output(
            tool_name="slack_post_message",
            ok=False,
            summary=msg,
            content_type="error",
            data={"channel": channel, "text": text},
            errors=[msg],
            metadata={"server_script_path": slack_server_path},
        )

    try:
        result = call_mcp_tool(
            server_script_path=slack_server_path,
            tool_name="post_message",
            arguments={"channel": channel, "text": text},
        )
        ok = not bool(result.get("isError")) if isinstance(result, dict) else True
        errors = ["Slack MCP server returned an error."] if isinstance(result, dict) and result.get("isError") else []
        return render_tool_output(
            tool_name="slack_post_message",
            ok=ok,
            summary=(
                f"Posted message to Slack channel '{channel}'."
                if ok
                else f"Failed to post message to Slack channel '{channel}'."
            ),
            content_type="delivery",
            data={"channel": channel, "text": text, "result": result},
            errors=errors,
            metadata={"server_script_path": slack_server_path},
        )
    except Exception:
        logger.exception("slack_post_message failed: channel=%s", channel)
        raise


__all__ = ["slack_post_message"]
