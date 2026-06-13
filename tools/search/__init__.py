"""Stable public API for tools.search — used by tools.mcp_server and tests."""
from tools.search.index import load_index, build_index, save_index
from tools.search.query import query, Hit

__all__ = ["load_index", "build_index", "save_index", "query", "Hit"]
