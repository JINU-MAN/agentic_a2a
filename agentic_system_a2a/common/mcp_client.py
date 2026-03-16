from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Dict

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

# PROJECT_ROOT points to the agentic_system_a2a package root
PROJECT_ROOT = Path(__file__).resolve().parents[2] / "agentic_system_a2a"


def _child_process_env(*, pythonpath_prepend: Path | None = None) -> Dict[str, str]:
    env = os.environ.copy()
    if pythonpath_prepend is not None:
        prepend = str(pythonpath_prepend)
        current = str(env.get("PYTHONPATH", "")).strip()
        env["PYTHONPATH"] = os.pathsep.join([prepend, current]) if current else prepend
    return env


def _resolve_server_script_path(server_script_path: str) -> Path:
    candidate = Path(str(server_script_path or "").strip())
    if candidate.is_absolute():
        return candidate.resolve()
    return (PROJECT_ROOT / candidate).resolve()


def _server_params(server_script_path: str) -> StdioServerParameters:
    """
    Build stdio server params from an MCP server path.
    """
    server_path = _resolve_server_script_path(server_script_path)

    if server_path.parent.name == "mcp_local" and server_path.name.endswith("_server.py"):
        # Standalone-friendly execution:
        # run package module and pin PYTHONPATH to package parent.
        project_root = server_path.parent.parent
        package_name = project_root.name
        module = f"{package_name}.mcp_local.{server_path.stem}"
        child_env = _child_process_env(pythonpath_prepend=project_root.parent)
        logger.debug(
            "server_params_resolved: module=%s project_root=%s",
            module,
            project_root,
        )
        return StdioServerParameters(
            command=sys.executable,
            args=["-m", module],
            env=child_env,
        )

    logger.debug("server_params_resolved: script=%s", server_path)
    return StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
        env=_child_process_env(),
    )


async def _async_call_mcp_tool(
    server_script_path: str,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute MCP server over stdio and call one tool.
    """
    logger.debug("mcp_tool_call_started: server=%s tool=%s", server_script_path, tool_name)

    async with AsyncExitStack() as stack:
        server_params = _server_params(server_script_path)
        stdio_transport = await stack.enter_async_context(stdio_client(server_params))
        read_stream, write_stream = stdio_transport

        session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
        await session.initialize()

        result = await session.call_tool(tool_name, arguments)
        dumped = result.model_dump(mode="json", exclude_none=True)
        logger.debug("mcp_tool_call_completed: tool=%s", tool_name)
        return dumped


def call_mcp_tool(
    server_script_path: str,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Sync wrapper that can be used from regular functions.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        logger.debug("call_mode: sync_asyncio_run tool=%s", tool_name)
        try:
            return asyncio.run(_async_call_mcp_tool(server_script_path, tool_name, arguments))
        except Exception as e:
            logger.exception(
                "mcp_tool_call_failed (sync_asyncio_run): server=%s tool=%s",
                server_script_path,
                tool_name,
            )
            raise

    result: Dict[str, Any] = {}
    error: Exception | None = None
    logger.debug("call_mode: threaded_event_loop tool=%s", tool_name)

    def _run_in_thread() -> None:
        nonlocal result, error
        try:
            result = asyncio.run(_async_call_mcp_tool(server_script_path, tool_name, arguments))
        except Exception as e:  # pragma: no cover
            error = e

    thread = threading.Thread(target=_run_in_thread, daemon=True)
    thread.start()
    thread.join()

    if error is not None:
        logger.exception(
            "mcp_tool_call_failed (threaded_event_loop): server=%s tool=%s",
            server_script_path,
            tool_name,
        )
        raise error

    logger.debug("mcp_tool_call_returned: tool=%s", tool_name)
    return result


__all__ = ["call_mcp_tool"]
