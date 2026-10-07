"""A small, responsive curses UI for the existing JSON to-do utilities."""

from __future__ import annotations

import curses
import json
import sys
import termios
from pathlib import Path
from typing import Any

from utils.add_todo import add_todo
from utils.delete_todo import delete_todo
from utils.edit_todo import edit_todo
from utils.rearrange_todos import rearrange_todos


# Edit these keys to customize the interface.
BINDINGS = {
    "enter_select": ("i", "\n", "\r"),
    "up": ("k",),
    "down": ("j",),
    "view": ("v",),
    "add": ("a",),
    "delete": ("d",),
    "edit": ("e",),
    "rearrange": ("r",),
    "cancel": ("q", "\x1b"),
    "confirm": ("y", "\n", "\r"),
    "save": ("\x13",),  # Ctrl+S
}


class TodoUI:
    def __init__(self, screen: Any, path: Path):
        self.screen = screen
        self.path = Path(path)
        self.categories: list[dict[str, Any]] = []
        self.category_index = 0
        self.todo_index = 0
        self.select_mode = False
        self.message = ""
        self.running = True
        self.colors = curses.has_colors()
        self._init_colors()

    def _init_colors(self) -> None:
        if self.colors:
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_CYAN, -1)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)

    def _attr(self, pair: int = 1) -> int:
        return curses.color_pair(pair) if self.colors else curses.A_REVERSE

    def load(self) -> None:
        try:
            with self.path.open(encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, list):
                raise ValueError("Expected a list of categories")
            self.categories = data[:9]
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            self.categories = []
            self.message = f"Could not read {self.path}: {exc}"
        self.category_index = min(self.category_index, max(0, len(self.categories) - 1))
        todos = self.current_todos
        self.todo_index = min(self.todo_index, max(0, len(todos) - 1))

    @property
    def current_category(self) -> dict[str, Any] | None:
        if not self.categories:
            return None
        return self.categories[self.category_index]

    @property
    def current_todos(self) -> list[dict[str, Any]]:
        category = self.current_category
        return category.get("toDos", []) if category else []

    @property
    def current_todo(self) -> dict[str, Any] | None:
        todos = self.current_todos
        return (
            todos[self.todo_index] if todos and self.todo_index < len(todos) else None
        )

    def run(self) -> None:
        self.screen.keypad(True)
        curses.curs_set(0)
        self.load()
        while self.running:
            self.draw()
            key = self.screen.get_wch()
            self.handle_key(key)

    def draw(self) -> None:
        self.screen.erase()
        height, width = self.screen.getmaxyx()
        if height < 7 or width < 30:
            self._put(0, 0, "Terminal too small; resize to at least 30x7.")
            self.screen.refresh()
            return

        x = 1
        for index, category in enumerate(self.categories[:9]):
            name = f"[{index + 1}] {category.get('categoryName', 'Category')}"
            attr = (
                self._attr(2)
                if index == self.category_index and self.colors
                else (
                    curses.A_REVERSE
                    if index == self.category_index
                    else curses.A_NORMAL
                )
            )
            if index == self.category_index and self.colors:
                attr = self._attr(2)
            if x < width - 1:
                self._put(0, x, name[: max(0, width - x - 1)], attr)
                x += len(name) + 2

        mode = "SELECT" if self.select_mode else "NORMAL"
        self._put(1, 1, f"{mode}  {self.message}"[: width - 2])
        top, bottom = 3, height - 3
        self._border(top, bottom, width)
        category = self.current_category
        title = category.get("categoryName", "Todos") if category else "No categories"
        self._put(top, 3, f" {title} ", self._attr())
        visible_height = bottom - top - 1
        start = max(0, self.todo_index - visible_height + 1)
        for row, todo_num in enumerate(
            range(start, min(len(self.current_todos), start + visible_height)),
            start=top + 1,
        ):
            todo = self.current_todos[todo_num]
            line = f"{todo_num + 1}. {todo.get('title', '')}"
            attr = (
                curses.A_REVERSE
                if self.select_mode and todo_num == self.todo_index
                else curses.A_NORMAL
            )
            self._put(row, 2, line[: max(0, width - 4)], attr)
        help_line = (
            "1-9 categories  i select  Esc quit"
            if not self.select_mode
            else "j/k move  a add  v view  d delete  e edit  r reorder  Esc back"
        )
        self._put(height - 1, 1, help_line[: width - 2])
        self.screen.refresh()

    def _put(self, y: int, x: int, value: str, attr: int = curses.A_NORMAL) -> None:
        height, width = self.screen.getmaxyx()
        if 0 <= y < height and 0 <= x < width:
            try:
                self.screen.addnstr(y, x, value, max(0, width - x - 1), attr)
            except curses.error:
                pass

    def _border(self, top: int, bottom: int, width: int) -> None:
        attr = self._attr(1)
        self._put(top, 1, "+" + "-" * max(0, width - 3) + "+", attr)
        self._put(bottom, 1, "+" + "-" * max(0, width - 3) + "+", attr)
        for y in range(top + 1, bottom):
            self._put(y, 1, "|", attr)
            self._put(y, width - 2, "|", attr)

    def _matches(self, key: Any, binding: str) -> bool:
        return key in BINDINGS[binding]

    def _report_error(self, message: str) -> None:
        self.message = message

    def handle_key(self, key: Any) -> None:
        if self._matches(key, "cancel"):
            if self.select_mode:
                self.select_mode = False
                self.message = "Normal mode"
            else:
                self.running = False
            return
        if not self.select_mode:
            if self._matches(key, "enter_select"):
                if self.current_category:
                    self.select_mode = True
                    self.message = "Select a to-do"
                return
            if isinstance(key, str) and key in "123456789":
                index = int(key) - 1
                if index < len(self.categories):
                    self.category_index = index
                    self.todo_index = 0
                    self.message = ""
            return

        if self._matches(key, "add"):
            self._add_modal()
        elif self._matches(key, "up"):
            self.todo_index = max(0, self.todo_index - 1)
        elif self._matches(key, "down"):
            self.todo_index = min(
                max(0, len(self.current_todos) - 1), self.todo_index + 1
            )
        elif self._matches(key, "view"):
            self._view_modal()
        elif self._matches(key, "delete"):
            self._delete_modal()
        elif self._matches(key, "edit"):
            self._edit_modal()
        elif self._matches(key, "rearrange"):
            self._rearrange_modal()

    def _modal(
        self, lines: list[str], fields: list[str] | None = None
    ) -> list[str] | None:
        fields = list(fields or [])
        height, width = self.screen.getmaxyx()
        box_w = min(width - 4, max(52, width * 85 // 100))
        box_h = min(height - 2, max(12, height * 3 // 4))
        top, left = (height - box_h) // 2, (width - box_w) // 2
        curses.curs_set(1 if fields else 0)
        for idx, line in enumerate(lines[: box_h - 2]):
            self._put(top + 1 + idx, left + 2, line[: box_w - 4])
        field_start = len(lines) + 1
        for i, value in enumerate(fields):
            self._put(top + field_start + i, left + 2, value[: box_w - 4])
        footer = (
            "Enter confirm   Esc cancel" if not fields else "Ctrl+N next   Esc cancel"
        )
        self._put(top + box_h - 2, left + 2, footer[: box_w - 4])
        for y in range(top, top + box_h):
            self._put(y, left, "|", self._attr())
            self._put(y, left + box_w - 1, "|", self._attr())
        self._put(top, left, "+" + "-" * (box_w - 2) + "+", self._attr())
        self._put(top + box_h - 1, left, "+" + "-" * (box_w - 2) + "+", self._attr())
        self.screen.refresh()
        if not fields:
            while True:
                key = self.screen.get_wch()
                if self._matches(key, "cancel") or self._matches(key, "confirm"):
                    return [] if self._matches(key, "confirm") else None
        result: list[str] = []
        for i, initial in enumerate(fields):
            y, x = top + field_start + i, left + 2
            value = initial
            while True:
                self._put(y, x, " " * max(0, box_w - 4))
                display_value = value.replace("\n", "↵")
                visible_value = display_value[-max(1, box_w - 5) :]
                self._put(y, x, visible_value)
                self.screen.move(y, min(width - 2, x + len(visible_value)))
                self.screen.refresh()
                key = self.screen.get_wch()
                if self._matches(key, "cancel"):
                    curses.curs_set(0)
                    return None
                if key == "\x0e":  # Ctrl+N
                    break
                if key in ("\n", "\r", curses.KEY_ENTER):
                    if i > 0:
                        value += "\n"
                    else:
                        curses.beep()
                    continue
                if key in (curses.KEY_BACKSPACE, "\b", "\x7f"):
                    value = value[:-1]
                elif isinstance(key, str) and key.isprintable():
                    value += key
            result.append(value)
        footer_y = top + box_h - 2
        self._put(footer_y, left + 2, " " * (box_w - 4))
        self._put(
            footer_y, left + 2, "Press Ctrl+S to save, Esc to cancel"[: box_w - 4]
        )
        self.screen.refresh()
        while True:
            key = self.screen.get_wch()
            if self._matches(key, "cancel"):
                curses.curs_set(0)
                return None
            if self._matches(key, "save"):
                break
        curses.curs_set(0)
        return result

    def _view_modal(self) -> None:
        todo = self.current_todo
        if not todo:
            return
        details = str(todo.get("details") or "(No details)")
        detail_lines = details.splitlines() or ["(No details)"]
        self._modal([str(todo.get("title", "")), "", *detail_lines])

    def _add_modal(self) -> None:
        category = self.current_category
        if not category:
            self.message = "No category selected"
            return
        values = self._modal(["Add a to-do to this category."], ["", ""])
        if values is None:
            return
        title, details = values
        if not title.strip():
            self.message = "Title cannot be empty"
            return
        todo = {"title": title, "details": details or None}
        self.message = ""
        if add_todo(category["id"], self.path, todo, on_error=self._report_error):
            self.load()
            self.todo_index = max(0, len(self.current_todos) - 1)
            self.message = "To-do added"
        else:
            self.message = self.message or "Add failed"

    def _delete_modal(self) -> None:
        todo, category = self.current_todo, self.current_category
        if not todo or not category:
            return
        confirmed = self._modal(
            [
                f"Delete '{todo.get('title', '')}'?",
                "Are you sure you want to delete this?",
                "Press Enter to confirm.",
            ]
        )
        if confirmed is not None:
            self.message = ""
            if delete_todo(
                category["id"], self.path, todo["id"], on_error=self._report_error
            ):
                self.message = "To-do deleted"
                self.load()
            else:
                self.message = self.message or "Delete failed"

    def _edit_modal(self) -> None:
        todo, category = self.current_todo, self.current_category
        if not todo or not category:
            return
        values = self._modal(
            ["Edit title and details (blank details clears them)."],
            [str(todo.get("title", "")), str(todo.get("details") or "")],
        )
        if values is not None:
            self.message = ""
            ok = edit_todo(
                category["id"],
                self.path,
                todo["id"],
                editTitle=values[0],
                editDetails=values[1],
                on_error=self._report_error,
            )
            self.message = "To-do saved" if ok else (self.message or "Edit failed")
            self.load()

    def _rearrange_modal(self) -> None:
        todo, category = self.current_todo, self.current_category
        if not todo or not category:
            return
        values = self._modal(
            [
                f"Move '{todo.get('title', '')}' to position 1-{len(self.current_todos)}."
            ],
            [str(self.todo_index + 1)],
        )
        if values is not None:
            try:
                place = int(values[0])
            except ValueError:
                self.message = "Enter a whole number"
                return
            self.message = ""
            if rearrange_todos(
                category["id"],
                self.path,
                todo["id"],
                place,
                on_error=self._report_error,
            ):
                self.todo_index = place - 1
                self.message = "To-do moved"
                self.load()
            else:
                self.message = self.message or "Reorder failed"


def _run(screen: Any, path: Path) -> None:
    curses.set_escdelay(25)
    terminal_fd = sys.stdin.fileno()
    original_attrs = termios.tcgetattr(terminal_fd)
    app_attrs = original_attrs.copy()
    app_attrs[0] &= ~termios.IXON
    termios.tcsetattr(terminal_fd, termios.TCSANOW, app_attrs)
    try:
        TodoUI(screen, path).run()
    finally:
        termios.tcsetattr(terminal_fd, termios.TCSANOW, original_attrs)


def start(path: str | Path | None = None) -> None:
    """Start the curses UI. Defaults to ``data/to-do-test.json`` in the cwd."""
    data_path = (
        Path(path) if path is not None else Path.cwd() / "data" / "to-do-test.json"
    )
    curses.wrapper(_run, data_path)
