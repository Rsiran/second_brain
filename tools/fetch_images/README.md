# tools/fetch_images

Localize remote images in a markdown file. Intended for use with Obsidian Web Clipper output.

## Usage

```bash
python -m tools.fetch_images raw/articles/my-article/index.md
```

For each `![alt](https://...)` or `<img src="https://...">`, downloads the image into `raw/articles/my-article/img/` and rewrites the markdown to use the local path. Idempotent: images already present are skipped.

## Filename policy

Downloaded files are named `<8-hex-url-hash>-<original-basename>.<ext>`, so URL collisions are avoided and repeated runs do not rename.
