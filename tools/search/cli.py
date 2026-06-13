from __future__ import annotations
import argparse
import sys
from pathlib import Path

from tools.search.index import build_index, save_index, load_index, index_is_stale
from tools.search.query import query as run_query


DEFAULT_INDEX = ".search-index/index.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.search")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_index = sub.add_parser("index", help="build or rebuild the search index")
    p_index.add_argument("--base", default=".", help="base directory")
    p_index.add_argument("--index", default=DEFAULT_INDEX, help="index file path")

    p_query = sub.add_parser("query", help="search the wiki")
    p_query.add_argument("terms", nargs="+")
    p_query.add_argument("--index", default=DEFAULT_INDEX)
    p_query.add_argument("--limit", type=int, default=20)
    p_query.add_argument("--type", choices=["source", "article", "index"], default=None)

    p_serve = sub.add_parser("serve", help="serve a tiny web UI for search")
    p_serve.add_argument("--index", default=DEFAULT_INDEX)
    p_serve.add_argument("--port", type=int, default=8080)

    args = parser.parse_args(argv)

    if args.cmd == "index":
        idx = build_index(args.base)
        save_index(idx, args.index)
        print(f"indexed {len(idx.documents)} files -> {args.index}")
        return 0

    if args.cmd == "query":
        if not Path(args.index).exists():
            print(f"error: index not found at {args.index}. Run 'index' first.", file=sys.stderr)
            return 2
        idx = load_index(args.index)
        # A stale index silently drops recent ingests from results; rebuild
        # (sub-second at this corpus size) so the primary research tool stays correct.
        if index_is_stale(args.index, idx.base_dir):
            idx = build_index(idx.base_dir)
            save_index(idx, args.index)
            print("note: search index was stale, rebuilt", file=sys.stderr)
        hits = run_query(idx, " ".join(args.terms), type_filter=args.type, limit=args.limit)
        if not hits:
            print("(no results)")
            return 0
        for h in hits:
            print(f"{h.score:6.2f}  {h.type:7}  {h.path}  —  {h.title}")
        return 0

    if args.cmd == "serve":
        from tools.search.server import serve
        serve(args.index, args.port)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
