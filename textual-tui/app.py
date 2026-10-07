"""Textual version of the personal to-do interface."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widgets import Input, Label, Static, TextArea
from rich.text import Text


# This folder has a hyphen in its name and is run directly from the project root.
# Add the project root so the existing utils package stays available.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.add_todo import add_todo
from utils.delete_todo import delete_todo
from utils.edit_todo import edit_todo
from utils.rearrange_todos import rearrange_todos


def _category_bindings() -> list[Binding]:
    return [
        Binding(key, f"select_category({index})", show=False)
        for index, key in enumerate("1234567890")
    ]


class TodoApp(App[None]):
    """Category-based to-do TUI with normal and select modes."""

    TITLE = "To-do"
    CSS = """
    Screen {
        background: #181818;
        color: #d6d6d6;
    }
    #app-frame {
        height: 1fr;
    }
    #categories {
        height: 2;
        padding: 0 1;
        overflow-x: hidden;
    }
    .category-tab {
        height: 1;
        width: auto;
        margin-right: 1;
        min-width: 0;
        padding: 0 1;
        background: #303030;
        color: #b8b8b8;
        content-align: left middle;
    }
    .category-tab.active {
        background: #d8d8d8;
        color: #181818;
        text-style: bold;
    }
    #status-bar {
        height: 2;
        padding: 0 2;
    }
    #mode {
        width: auto;
        height: 1;
        padding: 0 1;
        margin-right: 2;
        background: #303030;
        color: #e0e0e0;
        text-style: bold;
        content-align: left middle;
    }
    #status {
        width: 1fr;
        height: 2;
        padding: 0 1;
        color: #929292;
    }
    #todo-panel {
        height: 1fr;
        margin: 1 2;
        padding: 0 1;
        border: round #777777;
        background: #202020;
    }
    #todo-heading {
        height: 1;
        color: #e0e0e0;
        text-style: bold;
    }
    #todo-scroll {
        height: 1fr;
    }
    #todo-lines {
        width: 1fr;
    }
    #help {
        height: 2;
        padding: 0 2;
        color: #929292;
    }
    Input {
        border: round #686868;
        background: #202020;
        color: #d6d6d6;
    }
    Input:focus {
        border: round #d0d0d0;
    }
    TextArea {
        border: round #686868;
        background: #202020;
        color: #d6d6d6;
    }
    TextArea:focus {
        border: round #d0d0d0;
    }
    """

    BINDINGS = [
        *_category_bindings(),
        Binding("i", "enter_select", "Select mode"),
        Binding("enter", "enter_select", show=False),
        Binding("escape", "back", "Back / quit"),
        Binding("q", "back", show=False),
        Binding("j", "move_down", show=False),
        Binding("down", "move_down", show=False),
        Binding("k", "move_up", show=False),
        Binding("up", "move_up", show=False),
        Binding("a", "add_todo", "Add", show=False),
        Binding("v", "view_todo", "View", show=False),
        Binding("d", "delete_todo", "Delete", show=False),
        Binding("e", "edit_todo", "Edit", show=False),
        Binding("r", "rearrange_todo", "Reorder", show=False),
    ]

    def __init__(self, path: str | Path | None = None):
        super().__init__()
        self.register_theme(
            Theme(
                name="todo-gray",
                primary="#b0b0b0",
                secondary="#858585",
                warning="#c0c0c0",
                error="#d0d0d0",
                success="#a0a0a0",
                accent="#d8d8d8",
                foreground="#d6d6d6",
                background="#181818",
                surface="#242424",
                panel="#303030",
                boost="#404040",
                dark=True,
            )
        )
        self.theme = "todo-gray"
        self.path = Path(path) if path is not None else Path.cwd() / "data" / "to-do-test.json"
        self.categories: list[dict[str, Any]] = []
        self.category_index = 0
        self.todo_index = 0
        self.select_mode = False
        self.message = ""
        self._load_data()

    @property
    def current_category(self) -> dict[str, Any] | None:
        if not self.categories:
            return None
        return self.categories[self.category_index]

    @property
    def current_todos(self) -> list[dict[str, Any]]:
        category = self.current_category
        todos = category.get("toDos", []) if category else []
        return todos if isinstance(todos, list) else []

    @property
    def current_todo(self) -> dict[str, Any] | None:
        if 0 <= self.todo_index < len(self.current_todos):
            return self.current_todos[self.todo_index]
        return None

    def _load_data(self) -> None:
        try:
            with self.path.open(encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, list):
                raise ValueError("Expected a list of categories")
            self.categories = data
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            self.categories = []
            self.message = f"Could not read {self.path}: {exc}"
        self.category_index = min(self.category_index, max(0, len(self.categories) - 1))
        self.todo_index = min(self.todo_index, max(0, len(self.current_todos) - 1))

    def compose(self) -> ComposeResult:
        with Vertical(id="app-frame"):
            with Horizontal(id="categories"):
                if self.categories:
                    for index, category in enumerate(self.categories):
                        number = str((index + 1) % 10) if index < 10 else str(index + 1)
                        label = Text(f"{number}. {category.get('categoryName', 'Category')}")
                        classes = "category-tab active" if index == self.category_index else "category-tab"
                        yield Static(label, id=f"category-{index}", classes=classes)
                else:
                    yield Static("No categories", id="no-categories")
            with Horizontal(id="status-bar"):
                yield Static("NORMAL", id="mode", markup=False)
                yield Static(self.message, id="status", markup=False)
            with Vertical(id="todo-panel"):
                yield Static("Todos", id="todo-heading", markup=False)
                with VerticalScroll(id="todo-scroll"):
                    yield Static(id="todo-lines")
            yield Static("", id="help")

    def on_mount(self) -> None:
        self.refresh_view()

    def refresh_view(self) -> None:
        if not self.is_mounted:
            return
        category = self.current_category
        heading = category.get("categoryName", "Todos") if category else "Todos"
        self.query_one("#todo-heading", Static).update(Text(str(heading)))
        self.query_one("#mode", Static).update("SELECT" if self.select_mode else "NORMAL")
        self.query_one("#status", Static).update(Text(self.message))

        rendered = Text()
        if not self.current_todos:
            if category:
                rendered.append("No to-dos in this category.", style="dim")
        else:
            for index, todo in enumerate(self.current_todos):
                title = str(todo.get("title", "")).replace("\n", " ")
                line = Text(f"{index + 1}. {title}")
                if self.select_mode and index == self.todo_index:
                    line.stylize("bold black on #d8d8d8")
                rendered.append(line)
                if index < len(self.current_todos) - 1:
                    rendered.append("\n")
        self.query_one("#todo-lines", Static).update(rendered)
        self.query_one("#help", Static).update(
            "1-0 categories  i select  Esc quit"
            if not self.select_mode
            else "j/k move  a add  v view  d delete  e edit  r reorder  Esc back"
        )
        for index, category in enumerate(self.query(".category-tab")):
            category.set_class(index == self.category_index, "active")

    def _set_message(self, message: str) -> None:
        self.message = message
        if self.is_mounted:
            self.query_one("#status", Static).update(Text(message))

    def _report_error(self, message: str) -> None:
        self._set_message(f"Error: {message}")

    def action_select_category(self, index: int) -> None:
        if not self.select_mode and 0 <= index < len(self.categories):
            self.category_index = index
            self.todo_index = 0
            self._set_message("")
            self.refresh_view()

    def action_enter_select(self) -> None:
        if self.current_category:
            self.select_mode = True
            self.todo_index = min(self.todo_index, max(0, len(self.current_todos) - 1))
            self._set_message("Select a to-do")
            self.refresh_view()

    def action_back(self) -> None:
        if self.select_mode:
            self.select_mode = False
            self._set_message("Normal mode")
            self.refresh_view()
        else:
            self.exit()

    def action_move_down(self) -> None:
        if self.select_mode and self.current_todos:
            self.todo_index = min(len(self.current_todos) - 1, self.todo_index + 1)
            self.refresh_view()

    def action_move_up(self) -> None:
        if self.select_mode and self.current_todos:
            self.todo_index = max(0, self.todo_index - 1)
            self.refresh_view()

    def action_add_todo(self) -> None:
        if not self.select_mode or not self.current_category:
            return
        self.push_screen(
            FormDialog(
                "Add a to-do",
                [("Title", "", False), ("Details", "", True)],
            ),
            self._added_todo,
        )

    def _added_todo(self, values: list[str] | None) -> None:
        if values is None:
            return
        title, details = values
        if not title.strip():
            self._set_message("Title cannot be empty")
            return
        category = self.current_category
        self.message = ""
        if category and add_todo(
            category["id"], self.path, {"title": title, "details": details or None}, self._report_error
        ):
            self._load_data()
            self.todo_index = max(0, len(self.current_todos) - 1)
            self._set_message("To-do added")
            self.refresh_view()
        elif not self.message:
            self._set_message("Add failed")

    def action_view_todo(self) -> None:
        todo = self.current_todo
        if not self.select_mode or not todo:
            return
        title = str(todo.get("title", ""))
        details = str(todo.get("details") or "(No details)")
        self.push_screen(
            InfoDialog(title, "", body=details, confirm_label="Close")
        )

    def action_delete_todo(self) -> None:
        todo, category = self.current_todo, self.current_category
        if not self.select_mode or not todo or not category:
            return
        title = str(todo.get("title", ""))
        self.push_screen(
            InfoDialog(
                f"Delete {title}?",
                "Are you sure you want to delete this to-do?",
                confirm_label="Delete",
                destructive=True,
            ),
            lambda confirmed: self._deleted_todo(confirmed, category, todo),
        )

    def _deleted_todo(
        self, confirmed: bool | None, category: dict[str, Any], todo: dict[str, Any]
    ) -> None:
        if not confirmed:
            return
        self.message = ""
        if delete_todo(category["id"], self.path, todo["id"], self._report_error):
            self._load_data()
            self._set_message("To-do deleted")
            self.refresh_view()
        else:
            self._set_message(self.message or "Delete failed")

    def action_edit_todo(self) -> None:
        todo = self.current_todo
        if not self.select_mode or not todo:
            return
        self.push_screen(
            FormDialog(
                "Edit to-do",
                [
                    ("Title", str(todo.get("title", "")), False),
                    ("Details", str(todo.get("details") or ""), True),
                ],
            ),
            lambda values: self._edited_todo(values, todo),
        )

    def _edited_todo(self, values: list[str] | None, todo: dict[str, Any]) -> None:
        if values is None:
            return
        self.message = ""
        ok = edit_todo(
            self.current_category["id"],
            self.path,
            todo["id"],
            editTitle=values[0],
            editDetails=values[1],
            on_error=self._report_error,
        )
        if ok:
            self._load_data()
            self._set_message("To-do saved")
        else:
            self._set_message(self.message or "Edit failed")
        self.refresh_view()

    def action_rearrange_todo(self) -> None:
        todo = self.current_todo
        if not self.select_mode or not todo:
            return
        self.push_screen(
            FormDialog(
                "Reorder to-do",
                [(f"Position (1-{len(self.current_todos)})", str(self.todo_index + 1), False)],
            ),
            lambda values: self._rearranged_todo(values, todo),
        )

    def _rearranged_todo(self, values: list[str] | None, todo: dict[str, Any]) -> None:
        if values is None:
            return
        try:
            place = int(values[0])
        except ValueError:
            self._set_message("Enter a whole number")
            return
        category = self.current_category
        if category and rearrange_todos(
            category["id"], self.path, todo["id"], place, self._report_error
        ):
            self._load_data()
            self.todo_index = place - 1
            self._set_message("To-do moved")
        else:
            self._set_message(self.message or "Reorder failed")
        self.refresh_view()


class InfoDialog(ModalScreen[bool | None]):
    """View or confirm an action in a centered modal."""

    BINDINGS = [
        Binding("escape", "cancel", show=False, priority=True),
        Binding("enter", "confirm", show=False, priority=True),
    ]
    CSS = """
    InfoDialog {
        align: center middle;
        background: #101010 85%;
    }
    #dialog {
        width: 85%;
        height: 75%;
        max-width: 110;
        border: round #777777;
        background: #242424;
        padding: 1 2;
    }
    .dialog-title {
        height: auto;
        margin-bottom: 1;
        text-style: bold;
        color: #e0e0e0;
    }
    #dialog-message {
        height: auto;
        margin-bottom: 1;
    }
    #dialog-spacer {
        height: 1;
    }
    #dialog-body {
        height: 1fr;
    }
    #dialog-help {
        height: 2;
        padding-top: 1;
        color: #a0a0a0;
    }
    """

    def __init__(
        self,
        title: str,
        message: str,
        *,
        body: str | None = None,
        confirm_label: str = "Confirm",
        destructive: bool = False,
    ):
        super().__init__()
        self.title_text = title
        self.message_text = message
        self.body_text = body
        self.confirm_label = confirm_label
        self.destructive = destructive

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(self.title_text, classes="dialog-title", markup=False)
            yield Static(self.message_text, id="dialog-message", markup=False)
            if self.body_text is not None:
                yield Static("", id="dialog-spacer")
                with VerticalScroll(id="dialog-body"):
                    yield Static(self.body_text, markup=False)
            yield Static(
                "Enter close  ·  Esc cancel"
                if self.confirm_label == "Close"
                else "Enter confirm  ·  Esc cancel",
                id="dialog-help",
            )

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_confirm(self) -> None:
        self.dismiss(True)


class FormDialog(ModalScreen[list[str] | None]):
    """Edit one or more fields, then explicitly save with Ctrl+S."""

    BINDINGS = [
        Binding("escape", "cancel", show=False, priority=True),
        Binding("ctrl+n", "next_field", show=False, priority=True),
        Binding("ctrl+s", "save", show=False, priority=True),
    ]
    CSS = """
    FormDialog {
        align: center middle;
        background: #101010 85%;
    }
    #dialog {
        width: 85%;
        height: 75%;
        max-width: 110;
        border: round #777777;
        background: #242424;
        padding: 1 2;
    }
    .dialog-title {
        height: auto;
        margin-bottom: 1;
        text-style: bold;
        color: #e0e0e0;
    }
    .field-label {
        height: 1;
        margin-top: 1;
    }
    .field-input {
        height: 3;
    }
    .field-text-area {
        height: 1fr;
        min-height: 5;
    }
    #instructions {
        height: 2;
        padding-top: 1;
        color: #a0a0a0;
    }
    """

    def __init__(self, title: str, fields: list[tuple[str, str, bool]]):
        super().__init__()
        self.title_text = title
        self.fields = fields
        self.field_stage = 0
        self.ready_to_save = False

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(self.title_text, classes="dialog-title")
            for index, (label, value, multiline) in enumerate(self.fields):
                yield Label(label, classes="field-label")
                if multiline:
                    yield TextArea(value, id=f"field-{index}", classes="field-text-area")
                else:
                    yield Input(value, id=f"field-{index}", classes="field-input")
            yield Static("Ctrl+N: next field  ·  Esc: cancel", id="instructions")

    def on_mount(self) -> None:
        self.query_one("#field-0").focus()

    def action_next_field(self) -> None:
        if self.ready_to_save:
            return
        if self.field_stage + 1 < len(self.fields):
            self.field_stage += 1
            self.query_one(f"#field-{self.field_stage}").focus()
            instruction = "Ctrl+N: finish fields  ·  Esc: cancel"
        else:
            self.ready_to_save = True
            instruction = "Ctrl+S: save  ·  Esc: cancel"
        self.query_one("#instructions", Static).update(instruction)

    def action_save(self) -> None:
        if not self.ready_to_save:
            return
        values: list[str] = []
        for index, (_label, _initial, multiline) in enumerate(self.fields):
            if multiline:
                values.append(self.query_one(f"#field-{index}", TextArea).text)
            else:
                values.append(self.query_one(f"#field-{index}", Input).value)
        self.dismiss(values)

    def action_cancel(self) -> None:
        self.dismiss(None)


def start(path: str | Path | None = None) -> None:
    """Run the Textual interface using data/to-do-test.json by default."""
    TodoApp(path).run()


if __name__ == "__main__":
    start()
