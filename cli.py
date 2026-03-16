from __future__ import annotations

import asyncio
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest


BASE_URL = "http://localhost:8000"


def _extract_text(payload: dict) -> str:
    result = payload.get("result", {})
    for artifact in result.get("artifacts", []):
        for part in artifact.get("parts", []):
            if part.get("kind") == "text" and part.get("text"):
                return part["text"]
    for part in result.get("parts", []):
        if part.get("kind") == "text" and part.get("text"):
            return part["text"]
    status = result.get("status", {})
    msg = status.get("message", {})
    for part in msg.get("parts", []):
        if part.get("kind") == "text" and part.get("text"):
            return part["text"]
    return str(payload)


async def send_message(text: str, context_id: str) -> str:
    async with httpx.AsyncClient(timeout=180.0) as http:
        resolver = A2ACardResolver(httpx_client=http, base_url=BASE_URL)
        card = await resolver.get_agent_card()
        client = A2AClient(httpx_client=http, agent_card=card)
        req = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(message={
                "role": "user",
                "parts": [{"kind": "text", "text": text}],
                "messageId": uuid4().hex,
                "contextId": context_id,
            }),
        )
        resp = await client.send_message(req)
        return _extract_text(resp.model_dump(mode="json", exclude_none=True))


def main() -> None:
    context_id = uuid4().hex  # 세션 내내 고정
    print(f"MainAgent CLI — connected to {BASE_URL}")
    print(f"Session ID: {context_id}")
    print("Type your message and press Enter. Type 'exit' or Ctrl+C to quit.\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Bye.")
            break
        print("Agent: ", end="", flush=True)
        try:
            response = asyncio.run(send_message(user_input, context_id))
            print(response)
        except httpx.ConnectError:
            print(f"[error] Cannot connect to {BASE_URL}. Is the server running?")
        except Exception as exc:
            print(f"[error] {exc}")
        print()


if __name__ == "__main__":
    main()
