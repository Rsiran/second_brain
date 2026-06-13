# MCP integration

This KB ships an MCP server (`kb-mcp`) that exposes seven read-only tools to any MCP client — Claude Desktop, Claude Code, [Hermes Agent](https://hermes-agent.nousresearch.com/), or your own. The client spawns the server as a stdio subprocess and registers its tools (typically namespaced, e.g. `mcp_kb_*`).

## Setup

1. Install the `mcp` extra in the venv:

   ```bash
   uv pip install -e ".[mcp]"
   ```

2. Build the search index (one-time, plus whenever `wiki/` changes substantially):

   ```bash
   make search-index
   ```

3. Register the server with your MCP client. The command is `uv run --directory <repo> python -m tools.mcp_server` over stdio.

   **Claude Code** — from the repo root:

   ```bash
   claude mcp add kb -- uv run --directory "$(pwd)" python -m tools.mcp_server
   ```

   **Claude Desktop** — in `claude_desktop_config.json`:

   ```json
   {
     "mcpServers": {
       "kb": {
         "command": "uv",
         "args": ["run", "--directory", "/absolute/path/to/this/repo", "python", "-m", "tools.mcp_server"]
       }
     }
   }
   ```

   **Hermes Agent** — in `~/.hermes/config.yaml`:

   ```yaml
   mcp_servers:
     kb:
       command: "uv"
       args:
         - "run"
         - "--directory"
         - "/absolute/path/to/this/repo"
         - "python"
         - "-m"
         - "tools.mcp_server"
       timeout: 120
   ```

4. Restart the client. The `kb` server and its seven tools should appear.

## Tools

| Tool | Purpose |
|---|---|
| `get_contract` | Returns CLAUDE.md + CONTEXT.md. Call once per session before any other tool. |
| `search` | Full-text search over `wiki/`; returns slug/title/zone/path/snippet/score. |
| `get_article` | Read a wiki concept article by slug. |
| `get_source` | Read a source summary from `wiki/sources/`. |
| `list_index` | Read an index file (e.g. `by-topic`, `by-date`, `orphans`, or zone-scoped). |
| `ingest_status` | Show pending ingest work (new/modified/orphaned raw files). |
| `lint` | Wiki health check — errors and warnings. |

## Sensitivity

The MCP server is **read-only** and does not enforce the sensitivity policy server-side. The contract carrier is `get_contract` — agents are expected to call it at session start and respect the rules it returns. See [CLAUDE.md §1](../CLAUDE.md) for the full policy; whatever reaches `wiki/` is what the agent (and its model provider) can surface, so keep restricted material out of `wiki/` and `raw/` entirely.

## Writing deliverables

The MCP server has no write tools. Clients use their own filesystem tools to create output bundles in `out/YYYY-MM-DD-<slug>/` per [CLAUDE.md §4.2](../CLAUDE.md). The MCP server stays a retrieval-only surface; the filesystem is the integration boundary.
