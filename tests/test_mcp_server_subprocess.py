"""Smoke test: launch the MCP server as a subprocess and exchange MCP messages.

Catches packaging / entry-point regressions and verifies the FastMCP wire
protocol works end-to-end. Uses the official `mcp` SDK's stdio client
rather than hand-rolling JSON-RPC.
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

import pytest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


REPO = Path(__file__).resolve().parent.parent
EXPECTED_TOOLS = {
    "get_contract",
    "search",
    "get_article",
    "get_source",
    "list_index",
    "ingest_status",
    "lint",
}


async def _list_tools() -> set[str]:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "tools.mcp_server"],
        cwd=str(REPO),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resp = await session.list_tools()
            return {t.name for t in resp.tools}


def test_subprocess_lists_all_seven_tools():
    names = asyncio.run(_list_tools())
    assert names == EXPECTED_TOOLS, f"missing/extra: {names ^ EXPECTED_TOOLS}"


async def _call_get_contract() -> str:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "tools.mcp_server"],
        cwd=str(REPO),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_contract", {})
            # FastMCP packs the return value as text content
            return "".join(c.text for c in result.content if hasattr(c, "text"))


def test_subprocess_call_get_contract():
    out = asyncio.run(_call_get_contract())
    assert "Contract for the Knowledge Base" in out
