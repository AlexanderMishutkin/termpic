# termpic

Low-res terminal preview of a PNG/JPG. It's a preview, not a viewer, but it beats nothing
when all you have is a terminal or a chat that only renders text.

| mode    | looks like               | where it works                                  |
|---------|--------------------------|-------------------------------------------------|
| `ansi`  | truecolor `▀` half-blocks | a real terminal (`! termpic img.png` in Claude Code) |
| `emoji` | 🟥🟧🟨🟩🟦🟪🟫⬛⬜        | anywhere emoji render, incl. markdown/chat       |
| `ascii` | ` .:-=+*#%@`             | anywhere, monochrome                             |

## Run

```sh
uv sync
uv run termpic path/to/image.png                 # ansi, full terminal width
uv run termpic image.jpg -m emoji -w 60          # 30 emoji wide
uv run termpic image.png -m ascii -w 80 -H 30    # cap at 30 rows
```

Width defaults to `$COLUMNS`, then the attached terminal, then the nearest ancestor
process's terminal (so it works from captured subprocesses), then 80. `-f 0.3` uses 30% of it.

## Claude Code skill

`make install-skill` symlinks `skill/` into `~/.claude/skills/termpic`, so Claude can
drop emoji/ASCII previews of images straight into its replies.
