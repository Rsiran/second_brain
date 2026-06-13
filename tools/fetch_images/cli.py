from __future__ import annotations
import argparse
import sys
from pathlib import Path

import httpx

from tools.fetch_images.extract import extract_remote_image_urls
from tools.fetch_images.download import download_image
from tools.fetch_images.rewrite import rewrite_urls


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.fetch_images",
        description="Download remote images referenced by a markdown file.",
    )
    parser.add_argument("markdown", help="path to the markdown file")
    parser.add_argument(
        "--img-subdir", default="img",
        help="folder (relative to the markdown file) for downloaded images",
    )
    args = parser.parse_args(argv)

    md_path = Path(args.markdown).resolve()
    if not md_path.is_file():
        print(f"error: not a file: {md_path}", file=sys.stderr)
        return 2
    text = md_path.read_text(encoding="utf-8")
    urls = extract_remote_image_urls(text)
    if not urls:
        print("no remote images found")
        return 0

    img_dir = md_path.parent / args.img_subdir
    mapping: dict[str, str] = {}
    failures: list[tuple[str, str]] = []
    for url in urls:
        try:
            dest = download_image(url, img_dir)
        except (httpx.HTTPError, OSError) as e:
            failures.append((url, str(e)))
            print(f"  {url} -> FAILED: {e}", file=sys.stderr)
            continue
        rel = f"{args.img_subdir}/{dest.name}"
        mapping[url] = rel
        print(f"  {url} -> {rel}")

    # Rewrite whatever succeeded; a few dead image links must not discard the rest.
    new_text = rewrite_urls(text, mapping)
    if new_text != text:
        md_path.write_text(new_text, encoding="utf-8")
        print(f"rewrote {md_path}")

    if failures:
        print(f"{len(failures)} of {len(urls)} downloads failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
