from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional
from urllib import error, request

from mcp.server.fastmcp import FastMCP


logger = logging.getLogger(__name__)
mcp = FastMCP("slack-mcp-server", json_response=True)

SLACK_POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _get_slack_token() -> str:
    return (
        os.getenv("SLACK_BOT_TOKEN")
        or os.getenv("SLACK_API_TOKEN")
        or os.getenv("SLACK_TOKEN")
        or ""
    )


_load_env_file()


@mcp.tool()
def post_message(channel: str, text: str, thread_ts: Optional[str] = None) -> Dict[str, Any]:
    """
    Send a message to a Slack channel using chat.postMessage.
    """
    token = _get_slack_token()
    if not token:
        return {"ok": False, "error": "missing_slack_token",
                "message": "Set SLACK_BOT_TOKEN (or SLACK_API_TOKEN / SLACK_TOKEN)."}
    if not channel.strip():
        return {"ok": False, "error": "invalid_channel", "message": "channel is required."}
    if not text.strip():
        return {"ok": False, "error": "invalid_text", "message": "text is required."}

    payload: Dict[str, Any] = {"channel": channel, "text": text}
    if thread_ts:
        payload["thread_ts"] = thread_ts

    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        SLACK_POST_MESSAGE_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )

    try:
        with request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        return {"ok": False, "error": "http_error", "status_code": e.code, "response": raw}
    except error.URLError as e:
        return {"ok": False, "error": "network_error", "message": str(e.reason)}
    except Exception as e:
        return {"ok": False, "error": "unexpected_error", "message": str(e)}

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return {"ok": False, "error": "invalid_json_response", "response": raw}

    if not result.get("ok"):
        return {"ok": False, "error": result.get("error", "unknown_error"), "response": result}

    return {
        "ok": True,
        "channel": result.get("channel"),
        "ts": result.get("ts"),
        "message": result.get("message"),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
