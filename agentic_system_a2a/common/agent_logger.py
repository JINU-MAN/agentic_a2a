from __future__ import annotations

import json
import logging
import logging.handlers
from pathlib import Path
from typing import Any

LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
SESSION_LOG = LOGS_DIR / "session.log"

_FMT = "%(asctime)s %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"

_session_logger: logging.Logger | None = None


def _get_session_logger() -> logging.Logger:
    global _session_logger
    if _session_logger is not None:
        return _session_logger

    LOGS_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger("agentic.session")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.FileHandler(SESSION_LOG, mode="a", encoding="utf-8")
        handler.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
        logger.addHandler(handler)
    _session_logger = logger
    return logger


def setup_agent_logging(agent_name: str) -> dict[str, Any]:
    """
    Set up file logging for an agent and return ADK callbacks dict.

    Usage in agent.py:
        from ..common.agent_logger import setup_agent_logging
        callbacks = setup_agent_logging("MyAgent")
        agent = LlmAgent(..., **callbacks)
    """
    LOGS_DIR.mkdir(exist_ok=True)

    # Per-agent rotating log
    agent_logger = logging.getLogger(f"agentic.{agent_name}")
    agent_logger.setLevel(logging.DEBUG)
    agent_logger.propagate = False
    if not agent_logger.handlers:
        log_file = LOGS_DIR / f"{agent_name.lower()}.log"
        handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
        agent_logger.addHandler(handler)

    session_logger = _get_session_logger()

    def _log(event_type: str, body: str) -> None:
        line = f"[{agent_name}] {event_type:<12} | {body}"
        agent_logger.info(line)
        session_logger.info(line)

    def _parts_to_text(parts: list) -> str:
        texts = []
        for p in parts or []:
            text = getattr(p, "text", None)
            if text:
                texts.append(text)
        return " ".join(texts)

    # ── Callbacks ────────────────────────────────────────────────────────────

    def before_model_callback(callback_context, llm_request):
        contents = llm_request.contents or []
        for content in reversed(contents):
            if getattr(content, "role", None) == "user":
                text = _parts_to_text(content.parts)
                if text:
                    _log("USER_MSG", text[:600])
                break
        return None

    def after_model_callback(callback_context, llm_response):
        content = llm_response.content
        if content:
            text = _parts_to_text(content.parts)
            if text:
                _log("AGENT_RESP", text[:600])
        return None

    def before_tool_callback(tool, args, tool_context):
        try:
            args_str = json.dumps(args, ensure_ascii=False)
        except Exception:
            args_str = str(args)
        _log("TOOL_CALL", f"{tool.name} | {args_str[:400]}")
        return None

    def after_tool_callback(tool, args, tool_context, tool_response):
        try:
            resp_str = json.dumps(tool_response, ensure_ascii=False)
        except Exception:
            resp_str = str(tool_response)
        _log("TOOL_RESULT", f"{tool.name} | {resp_str[:400]}")
        return None

    return {
        "before_model_callback": before_model_callback,
        "after_model_callback": after_model_callback,
        "before_tool_callback": before_tool_callback,
        "after_tool_callback": after_tool_callback,
    }


__all__ = ["setup_agent_logging"]
