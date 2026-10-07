# Textual to-do TUI

Run from the project root:

```sh
uv run python textual-tui
```

The interface is keyboard-only and uses a grayscale theme.

In normal mode, use `1`–`9` and `0` to switch categories, `i` to enter select
mode, and `Esc` to quit. In select mode, use `j`/`k` to move and `a`, `v`,
`d`, `e`, or `r` to add, view, delete, edit, or reorder a to-do. `Esc` returns
to normal mode.

In form modals, `Ctrl+N` advances through the fields and `Ctrl+S` saves after
all fields have been visited. Details support multiple lines; titles are
single-line. `Esc` cancels a modal.
