# Textual to-do TUI

Run from the project root:

```sh
uv run python textual-tui
```

The interface is keyboard-only and uses a grayscale theme.

In normal mode, use `1`–`9` to switch categories, `a` to add a category, `d`
to delete the selected category, and `r` to move it to a numbered position.
Use `0` to open weekly tasks, `i` to enter select mode, and `Esc` to quit. The
app supports up to nine categories. In select
mode, use `j`/`k` to move and `a`, `v`, `d`, `e`, or `r` to add, view, delete,
edit, or reorder a to-do. `Esc` returns to normal mode. Category data keeps the
existing JSON structure: a list of objects with `id`, `categoryName`, and
`toDos` fields. New IDs are lowercase slugs from the category name (for
example, `To Do` becomes `to-do`); duplicate IDs are rejected. Categories after
the ninth entry are ignored by the app.

Weekly tasks are stored in `data/weekly-tasks.json`. The date range starts at
the current Monday through Sunday and is shown without the year. Press `i` to
enter insert mode; use `j`/`k` to move, `a` to add a task, `Space` to toggle
its checkbox, `d` to remove it, `e` to edit the start and end dates as
`YYYY-MM-DD`, and `r` to move it to a numbered position. `Esc` first returns
to weekly normal mode, then returns to the to-do categories. Changing the date
range leaves task completion states as they are.

Press `Ctrl+J` from normal to-do mode to open the date-specific to-do list in
`data/todo-on-day-x.json`. Its selected date is stored as `YYYY-MM-DD` and
displayed without the year. In normal day mode, `e` opens a keyboard-operated
calendar: `h`/`l` move by a day, `k`/`j` by a week, and `H`/`L` by a month.
`S` selects today, `Enter` chooses the highlighted date, and `Esc` cancels.
Press `i` to select items, then use `a`, `v`, `d`, `e`, or `r` to add, view,
delete, edit, or reorder them. `Esc` returns to normal mode, then back to the
category to-dos.

In form modals, `Ctrl+N` advances through the fields, `Ctrl+L` returns to the
previous field, and `Ctrl+S` saves after all fields have been visited. Details
support multiple lines; titles are single-line. `Esc` cancels a modal.
