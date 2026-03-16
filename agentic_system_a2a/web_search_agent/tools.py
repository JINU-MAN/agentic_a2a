from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from ..common.mcp_client import call_mcp_tool
from ..common.tool_output_utils import render_tool_output


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
WEB_SEARCH_MCP_SERVER = BASE_DIR / "mcp_local" / "web_search_server.py"
DEFAULT_RESULT_COUNT = 6


def _extract_error_text(raw: Dict[str, Any]) -> str:
    messages: List[str] = []
    for item in raw.get("content", []):
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            messages.append(text.strip())
    return "\n".join(messages).strip()


def _extract_mcp_list_result(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    if raw.get("isError"):
        message = _extract_error_text(raw) or "MCP tool returned an error."
        return [{"error": message}]

    structured = raw.get("structuredContent", {})
    if isinstance(structured, dict):
        result = structured.get("result")
        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict)]

    content = raw.get("content")
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict):
            text = first.get("text")
            if isinstance(text, str):
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, list):
                        return [item for item in parsed if isinstance(item, dict)]
                except json.JSONDecodeError:
                    pass
    return []


def search_web_with_mcp(query: str, max_results: int = DEFAULT_RESULT_COUNT) -> str:
    """
    Query the web-search MCP server and return the shared tool output contract.
    """
    safe_query = query.strip()
    safe_max_results = max(1, min(int(max_results), 10))
    logger.debug("search_web_with_mcp: query=%s max_results=%d", safe_query, safe_max_results)
    try:
        raw = call_mcp_tool(
            server_script_path=str(WEB_SEARCH_MCP_SERVER),
            tool_name="search_web",
            arguments={"query": safe_query, "max_results": safe_max_results},
        )
        normalized = _extract_mcp_list_result(raw)
        error_messages = [
            str(item.get("error", "")).strip()
            for item in normalized
            if isinstance(item, dict) and str(item.get("error", "")).strip()
        ]
        items = [item for item in normalized if not (isinstance(item, dict) and item.get("error"))]
        ok = not error_messages
        summary = (
            f"Collected {len(items)} web result(s) for query '{safe_query}'."
            if ok
            else (error_messages[0] if error_messages else "Web search failed.")
        )
        result_text = render_tool_output(
            tool_name="search_web_with_mcp",
            ok=ok,
            summary=summary,
            content_type="collection",
            items=items,
            data={
                "query": safe_query,
                "requested_max_results": safe_max_results,
                "result_count": len(items),
            },
            errors=error_messages,
            metadata={"server_script_path": str(WEB_SEARCH_MCP_SERVER)},
        )
        logger.debug(
            "search_web_with_mcp completed: query=%s result_count=%d ok=%s",
            safe_query,
            len(items),
            ok,
        )
        return result_text
    except Exception as e:
        logger.exception("search_web_with_mcp failed: query=%s", safe_query)
        raise


__all__ = ["search_web_with_mcp"]
