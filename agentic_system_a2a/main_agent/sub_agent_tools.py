from __future__ import annotations

import asyncio
import concurrent.futures
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest


def _extract_a2a_text(payload: dict) -> str:
    result = payload.get("result", {})
    # Task artifact format
    for artifact in result.get("artifacts", []):
        for part in artifact.get("parts", []):
            if part.get("kind") == "text" and part.get("text"):
                return part["text"]
    # Message format
    for part in result.get("parts", []):
        if part.get("kind") == "text" and part.get("text"):
            return part["text"]
    # status message format
    status = result.get("status", {})
    msg = status.get("message", {})
    for part in msg.get("parts", []):
        if part.get("kind") == "text" and part.get("text"):
            return part["text"]
    return str(payload)


async def _async_call_a2a(base_url: str, message: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as http:
        resolver = A2ACardResolver(httpx_client=http, base_url=base_url)
        card = await resolver.get_agent_card()
        client = A2AClient(httpx_client=http, agent_card=card)
        req = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(message={
                "role": "user",
                "parts": [{"kind": "text", "text": message}],
                "messageId": uuid4().hex,
            }),
        )
        resp = await client.send_message(req)
        return _extract_a2a_text(resp.model_dump(mode="json", exclude_none=True))


def _call_a2a_sync(base_url: str, message: str) -> str:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _async_call_a2a(base_url, message))
                return future.result()
        return loop.run_until_complete(_async_call_a2a(base_url, message))
    except RuntimeError:
        return asyncio.run(_async_call_a2a(base_url, message))


def call_web_search_agent(query: str) -> str:
    """Search the web for current information, news, URLs, or general knowledge queries."""
    return _call_a2a_sync("http://localhost:8001", query)


def call_paper_agent(query: str) -> str:
    """Search academic papers and research documents in the local corpus or by DOI/arXiv ID."""
    return _call_a2a_sync("http://localhost:8002", query)


def call_sns_agent(keyword: str) -> str:
    """Search social media posts and trends for a keyword or topic."""
    return _call_a2a_sync("http://localhost:8003", keyword)


__all__ = ["call_web_search_agent", "call_paper_agent", "call_sns_agent"]
