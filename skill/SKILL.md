---
name: termpic
description: Show an image (PNG/JPG — a screenshot, chart, generated plot, design export) inline in a text reply as a low-res emoji or ASCII preview. Use when the user asks to "show", "preview" or "draw" an image in the terminal/chat, or when a quick visual of an image you just produced or read would help the user and an Artifact would be overkill.
---

# termpic

Renders an image as text you can paste into your reply. The CLI lives next to this file's
real location (`skill/` is symlinked from the termpic repo); resolve it with:

```sh
TERMPIC_DIR="$(dirname "$(readlink -f ~/.claude/skills/termpic)")"
uv run --project "$TERMPIC_DIR" termpic <image> -m emoji -w 60
```

## Choosing a mode

- **emoji** (default for replies): colored squares, survive markdown. Paste the output as
  plain lines, **not** in a code block (code blocks can break emoji width). 9-color palette,
  so it's a silhouette/color-blocking preview, not a photo.
- **ascii**: monochrome, finer detail. Paste inside a ```` ``` ```` code block.
- **ansi**: truecolor escape codes; your reply text can't carry them. Instead tell the user
  to run `! uv run --project <dir> termpic <image>` so it prints in their terminal directly.

## Sizing

Your Bash tool has no TTY, so terminal width auto-detection falls back to 80. Pass `-w`
explicitly: `-w 60` for emoji (= 30 squares; each is 2 columns), `-w 80` for ascii.
Add `-H 20`-ish to cap tall images. Keep previews ≤ ~25 rows so the reply stays readable.

Transparent PNGs flatten onto black; use `--bg 255,255,255` for light-on-transparent images.

## Rules

- Say it's a low-res preview and give the image path (or offer an Artifact) for the real thing.
- Never render images containing PHI or other sensitive data — the preview is still a copy.
