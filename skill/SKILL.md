---
name: termpic
description: Show an image (PNG/JPG — a screenshot, chart, generated plot, design export) inline in a text reply as a low-res emoji or ASCII preview. Use when the user asks to "show", "preview" or "draw" an image in the terminal/chat, or when a quick visual of an image you just produced or read would help the user and an Artifact would be overkill.
---

# termpic

Renders an image as text you can paste into your reply. The CLI lives next to this file's
real location (`skill/` is symlinked from the termpic repo); resolve it with:

```sh
TERMPIC_DIR="$(dirname "$(readlink -f ~/.claude/skills/termpic)")"
uv run --project "$TERMPIC_DIR" termpic <image> -m emoji -f 0.25
```

## Choosing a mode

- **emoji** (default for replies): colored squares, survive markdown. Paste the output as
  plain lines, **not** in a code block (code blocks can break emoji width). 9 colors picked
  by hue with brightness stretched to the image's own range, so it's a color-blocking
  preview, not a photo.
- **ascii**: monochrome, finer detail. Paste inside a ```` ``` ```` code block.
- **ansi**: truecolor escape codes; your reply text can't carry them. Instead tell the user
  to run `! uv run --project <dir> termpic <image>` so it prints in their terminal directly.

## Sizing

Width is auto-detected from the user's terminal (found via parent processes, since your
Bash tool has no TTY). Size with `-f <fraction of screen width>`: the user allows up to
`0.5`; default to `0.2`–`0.3` so the picture sits in the text instead of dominating it.
Emoji squares are 2 columns each. Add `-H 25`-ish to cap tall images. `-w <cols>` overrides.

Transparent PNGs flatten onto black; use `--bg 255,255,255` for light-on-transparent images.

## Rules

- Say it's a low-res preview and give the image path (or offer an Artifact) for the real thing.
- Never render images containing PHI or other sensitive data — the preview is still a copy.
