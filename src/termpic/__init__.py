"""Render an image as a low-res terminal preview.

Modes:
  ansi   truecolor half-blocks (▀), 2 pixels per cell; needs a real terminal.
  emoji  colored squares (🟥🟩🟦…); survives markdown, so it can be pasted into chat.
  ascii  grayscale character ramp; plain text, works anywhere.
"""

from __future__ import annotations

import argparse
import colorsys
import os
import shutil
import sys

from PIL import Image, ImageOps

ASCII_RAMP = " .:-=+*#%@"

# Terminal cells are roughly twice as tall as they are wide.
CELL_ASPECT = 0.5


def _ancestor_tty_size() -> os.terminal_size | None:
    # Captured subprocesses (e.g. an agent's shell tool) have no TTY of their own,
    # but the process that spawned them usually still holds the user's terminal.
    pid = os.getpid()
    while pid > 1:
        for fd in (1, 0, 2):
            try:
                target = os.readlink(f"/proc/{pid}/fd/{fd}")
            except OSError:
                continue
            if target.startswith(("/dev/pts/", "/dev/tty")):
                try:
                    tty = os.open(target, os.O_RDONLY | os.O_NOCTTY)
                    try:
                        return os.get_terminal_size(tty)
                    finally:
                        os.close(tty)
                except OSError:
                    continue
        try:
            with open(f"/proc/{pid}/stat") as f:
                pid = int(f.read().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            return None
    return None


def terminal_width() -> int:
    if cols := os.environ.get("COLUMNS"):
        return int(cols)
    for fd in (sys.stdout, sys.stderr, sys.stdin):
        try:
            return os.get_terminal_size(fd.fileno()).columns
        except (OSError, ValueError):
            continue
    if size := _ancestor_tty_size():
        return size.columns
    return shutil.get_terminal_size((80, 24)).columns


def _fit(img: Image.Image, cols: int, max_rows: int | None, px_per_row: float) -> Image.Image:
    """Resize to `cols` pixels wide, at most `max_rows` pixels tall, keeping on-screen aspect."""
    w, h = img.size
    rows = h / w * cols * px_per_row
    if max_rows and rows > max_rows:
        cols, rows = max(1, int(cols * max_rows / rows)), max_rows
    return img.resize((max(1, cols), max(1, round(rows))), Image.LANCZOS)


def _flatten(img: Image.Image, bg: tuple[int, int, int]) -> Image.Image:
    img = img.convert("RGBA")
    base = Image.new("RGBA", img.size, (*bg, 255))
    return Image.alpha_composite(base, img).convert("RGB")


def render_ansi(img: Image.Image, cols: int, max_rows: int | None) -> str:
    # Each cell holds two vertical pixels, so pixel rows = 2 * cell rows.
    small = _fit(img, cols, max_rows and max_rows * 2, CELL_ASPECT * 2)
    w, h = small.size
    px = small.load()
    lines = []
    for y in range(0, h, 2):
        parts = []
        for x in range(w):
            r1, g1, b1 = px[x, y]
            if y + 1 < h:
                r2, g2, b2 = px[x, y + 1]
                parts.append(f"\x1b[38;2;{r1};{g1};{b1}m\x1b[48;2;{r2};{g2};{b2}m▀")
            else:
                parts.append(f"\x1b[49m\x1b[38;2;{r1};{g1};{b1}m▀")
        lines.append("".join(parts) + "\x1b[0m")
    return "\n".join(lines)


def _percentile(sorted_values: list[float], q: float) -> float:
    return sorted_values[min(len(sorted_values) - 1, int(q * len(sorted_values)))]


def _emoji_for(hue: float, sat: float, val: float) -> str:
    """Pick a square by hue; `sat`/`val` are already normalized to the image's own range."""
    if val < 0.12:
        return "⬛"
    if sat < 0.28:
        return "⬛" if val < 0.35 else "🟫" if val < 0.5 else "⬜"
    deg = hue * 360
    if deg < 18 or deg >= 330:
        return "🟥" if val > 0.35 else "🟫"
    if deg < 40:
        return "🟧" if val > 0.45 else "🟫"
    if deg < 65:
        return "🟨" if val > 0.6 else "🟧" if val > 0.4 else "🟩" if deg > 52 else "🟫"
    if deg < 170:
        return "🟩"
    if deg < 260:
        return "🟦"
    return "🟪"


def render_emoji(img: Image.Image, cols: int, max_rows: int | None) -> str:
    # Emoji are double-width and square, so half the columns and no aspect squash.
    small = _fit(img, max(1, cols // 2), max_rows, 1.0)
    w, h = small.size
    px = small.load()
    hsv = [[colorsys.rgb_to_hsv(*(c / 255 for c in px[x, y])) for x in range(w)] for y in range(h)]
    # Only 9 colors: stretch to the image's own range, or dark photos collapse to all-black.
    vals = sorted(v for row in hsv for _, _, v in row)
    sats = sorted(s for row in hsv for _, s, _ in row)
    v_lo, v_hi = _percentile(vals, 0.03), _percentile(vals, 0.97)
    s_hi = max(1e-6, _percentile(sats, 0.95))
    v_span = max(1e-6, v_hi - v_lo)
    return "\n".join(
        "".join(_emoji_for(hh, s / s_hi, (v - v_lo) / v_span) for hh, s, v in row) for row in hsv
    )


def render_ascii(img: Image.Image, cols: int, max_rows: int | None, invert: bool) -> str:
    small = ImageOps.autocontrast(_fit(img, cols, max_rows, CELL_ASPECT).convert("L"), cutoff=2)
    w, h = small.size
    px = small.load()
    ramp = ASCII_RAMP[::-1] if invert else ASCII_RAMP
    last = len(ramp) - 1
    return "\n".join(
        "".join(ramp[px[x, y] * last // 255] for x in range(w)).rstrip() for y in range(h)
    )


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="termpic", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image")
    p.add_argument("-m", "--mode", choices=["ansi", "emoji", "ascii"], default="ansi")
    p.add_argument("-w", "--width", type=int, help="columns to use (default: terminal width)")
    p.add_argument("-f", "--fraction", type=float, default=1.0, help="share of terminal width when -w is not given")
    p.add_argument("-H", "--max-rows", type=int, help="cap output height in text rows")
    p.add_argument("--bg", default="0,0,0", help="R,G,B to flatten transparency onto (default 0,0,0)")
    p.add_argument("--invert", action="store_true", help="ascii: dense chars for dark pixels (light terminals)")
    args = p.parse_args(argv)

    bg = tuple(int(c) for c in args.bg.split(","))
    img = _flatten(Image.open(args.image), bg)  # type: ignore[arg-type]
    cols = args.width or max(1, int(terminal_width() * args.fraction))

    if args.mode == "ansi":
        out = render_ansi(img, cols, args.max_rows)
    elif args.mode == "emoji":
        out = render_emoji(img, cols, args.max_rows)
    else:
        out = render_ascii(img, cols, args.max_rows, args.invert)
    print(out)
