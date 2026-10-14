"""Textual version of the personal to-do interface."""

from __future__ import annotations

import calendar
import json
import sys
from datetime import date
from fractions import Fraction
from pathlib import Path
from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.geometry import NULL_OFFSET, Region, Size
from textual.layout import Layout, WidgetPlacement
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widgets import Input, Label, Static, TextArea
from textual.widget import Widget
from rich.text import Text

# This folder has a hyphen in its name and is run directly from the project root.
# Add the project root so the existing utils package stays available.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
WEEKLY_UTILS = PROJECT_ROOT / "utils" / "weekly-tasks"
if str(WEEKLY_UTILS) not in sys.path:
    sys.path.insert(0, str(WEEKLY_UTILS))
DAY_TODO_UTILS = PROJECT_ROOT / "utils" / "todo-on-day-x"
if str(DAY_TODO_UTILS) not in sys.path:
    sys.path.insert(0, str(DAY_TODO_UTILS))

from utils.add_todo import add_todo
from utils.add_category import add_category
from utils.delete_category import delete_category
from utils.delete_todo import delete_todo
from utils.edit_todo import edit_todo
from utils.rearrange_categories import rearrange_categories
from utils.rearrange_todos import rearrange_todos
from weekly_tasks import (
    add_weekly_task,
    delete_weekly_task,
    load_weekly_tasks,
    rearrange_weekly_task,
    set_weekly_dates,
    toggle_weekly_task,
)
from todo_on_day_x import (
    add_day_todo,
    delete_day_todo,
    edit_day_todo,
    load_day_todos,
    rearrange_day_todo,
    set_day_date,
)

MONTH_ABBREVIATIONS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


class CategoryWrapLayout(Layout):
    """Place category tabs in a natural left-to-right flow that wraps by row."""

    name = "category-wrap"

    def __init__(self, horizontal_gap: int = 1, row_gap: int = 1) -> None:
        self.horizontal_gap = horizontal_gap
        self.row_gap = row_gap

    def arrange(
        self,
        parent: Widget,
        children: list[Widget],
        size: Size,
        greedy: bool = True,
    ) -> list[WidgetPlacement]:
        parent.pre_layout(self)
        viewport = parent.app.viewport_size
        placements: list[WidgetPlacement] = []
        x = y = row_height = 0
        row_has_children = False

        for child in children:
            box = child._get_box_model(
                size,
                viewport,
                Fraction(size.width),
                Fraction(size.height),
                constrain_width=True,
                greedy=greedy,
            )
            width, height = int(box.width), int(box.height)
            margin = box.margin
            gap = self.horizontal_gap if row_has_children else 0
            outer_width = margin.left + width + margin.right

            if row_has_children and x + gap + outer_width > size.width:
                x = 0
                y += row_height + self.row_gap
                row_height = 0
                row_has_children = False
                gap = 0

            x += gap + margin.left
            placements.append(
                WidgetPlacement(
                    Region(x, y + margin.top, width, height),
                    NULL_OFFSET,
                    margin,
                    child,
                )
            )
            x += width + margin.right
            row_height = max(row_height, margin.top + height + margin.bottom)
            row_has_children = True

        return placements


class CategoryTabBar(Widget):
    """A category tab container using a wrapping flow layout."""

    DEFAULT_CSS = """
    CategoryTabBar {
        width: 1fr;
        height: auto;
        overflow: hidden hidden;
    }
    """

    def __init__(self, *children: Widget, **kwargs: Any) -> None:
        super().__init__(*children, **kwargs)
        self._default_layout = CategoryWrapLayout()


def _category_bindings() -> list[Binding]:
    return [
        Binding(key, f"select_category({index})", show=False)
        for index, key in enumerate("123456789")
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
        height: auto;
        padding: 0 1;
        margin-bottom: 2;
        overflow-x: hidden;
    }
    #categories.hidden {
        display: none;
    }
    #no-categories {
        display: none;
        height: 1;
        padding: 0 1;
        color: #929292;
    }
    #no-categories.visible {
        display: block;
    }
    #section-header {
        display: none;
        height: 2;
        padding: 0 2;
        margin-bottom: 1;
        color: #e0e0e0;
        text-style: bold;
        content-align: left middle;
    }
    #section-header.visible {
        display: block;
    }
    .category-tab {
        height: 1;
        width: auto;
        max-width: 100%;
        padding: 0 1;
        background: #303030;
        color: #b8b8b8;
        content-align: left middle;
    }
    .category-tab.hidden {
        display: none;
    }
    .category-tab.active {
        background: #d8d8d8;
        color: #181818;
        text-style: bold;
    }
    #status-bar {
        height: 2;
        padding: 0 2;
        margin-bottom: 1;
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
        margin: 0 2 1 2;
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
        Binding("0", "enter_weekly", "Weekly tasks"),
        Binding("ctrl+j", "enter_day_todos", "To-dos for a day"),
        Binding("i", "enter_select", "Select / insert mode"),
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
        Binding("space", "toggle_weekly_task", "Toggle done", show=False),
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
        self.path = (
            Path(path) if path is not None else Path.cwd() / "data" / "to-do-test.json"
        )
        self.weekly_path = PROJECT_ROOT / "data" / "weekly-tasks.json"
        self.day_todos_path = PROJECT_ROOT / "data" / "todo-on-day-x.json"
        self.categories: list[dict[str, Any]] = []
        self.category_index = 0
        self.todo_index = 0
        self.select_mode = False
        self.weekly_mode = False
        self.weekly_insert_mode = False
        self.weekly_index = 0
        self.weekly_data: dict[str, Any] = {
            "start_date": "",
            "end_date": "",
            "items": [],
        }
        self.day_todos_mode = False
        self.day_select_mode = False
        self.day_todo_index = 0
        self.day_data: dict[str, Any] = {"date": date.today().isoformat(), "toDos": []}
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

    @property
    def current_weekly_items(self) -> list[dict[str, Any]]:
        items = self.weekly_data.get("items", [])
        return items if isinstance(items, list) else []

    @property
    def current_weekly_task(self) -> dict[str, Any] | None:
        if 0 <= self.weekly_index < len(self.current_weekly_items):
            return self.current_weekly_items[self.weekly_index]
        return None

    @property
    def current_day_todos(self) -> list[dict[str, Any]]:
        todos = self.day_data.get("toDos", [])
        return todos if isinstance(todos, list) else []

    @property
    def current_day_todo(self) -> dict[str, Any] | None:
        if 0 <= self.day_todo_index < len(self.current_day_todos):
            return self.current_day_todos[self.day_todo_index]
        return None

    def _load_data(self) -> None:
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
        self.todo_index = min(self.todo_index, max(0, len(self.current_todos) - 1))

    def compose(self) -> ComposeResult:
        with Vertical(id="app-frame"):
            with CategoryTabBar(id="categories"):
                yield Static("No categories", id="no-categories", classes="visible")
                for index in range(9):
                    yield Static(
                        "", id=f"category-{index}", classes="category-tab hidden"
                    )
            yield Static("", id="section-header", markup=False)
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
        if self.weekly_mode:
            heading = "Weekly tasks"
        elif self.day_todos_mode:
            heading = "To-do on day x"
        else:
            heading = category.get("categoryName", "Todos") if category else "Todos"
        self.query_one("#todo-heading", Static).update(Text(str(heading)))
        if self.weekly_mode:
            mode_label = "INSERT" if self.weekly_insert_mode else "NORMAL"
        elif self.day_todos_mode:
            mode_label = "SELECT" if self.day_select_mode else "NORMAL"
        else:
            mode_label = "SELECT" if self.select_mode else "NORMAL"
        self.query_one("#mode", Static).update(mode_label)
        self.query_one("#status", Static).update(Text(self.message))
        section_mode = self.weekly_mode or self.day_todos_mode
        self.query_one("#categories").set_class(section_mode, "hidden")
        section_header = self.query_one("#section-header", Static)
        section_header.set_class(section_mode, "visible")
        if self.weekly_mode:
            section_header.update(self._format_week_range())
        elif self.day_todos_mode:
            section_header.update(self._format_day_date())

        rendered = Text()
        if self.weekly_mode:
            if not self.current_weekly_items:
                rendered.append("No weekly tasks yet.", style="dim")
            else:
                for index, task in enumerate(self.current_weekly_items):
                    checkbox = "[x]" if task.get("done") else "[ ]"
                    line = Text(f"{index + 1}. {checkbox} {task.get('name', '')}")
                    if task.get("done"):
                        line.stylize("dim strike")
                    if self.weekly_insert_mode and index == self.weekly_index:
                        line.stylize("bold black on #d8d8d8")
                    rendered.append(line)
                    if index < len(self.current_weekly_items) - 1:
                        rendered.append("\n")
        elif self.day_todos_mode:
            if not self.current_day_todos:
                rendered.append("Nothing to do", style="dim")
            else:
                for index, todo in enumerate(self.current_day_todos):
                    title = str(todo.get("title", "")).replace("\n", " ")
                    line = Text(f"{index + 1}. {title}")
                    if self.day_select_mode and index == self.day_todo_index:
                        line.stylize("bold black on #d8d8d8")
                    rendered.append(line)
                    if index < len(self.current_day_todos) - 1:
                        rendered.append("\n")
        elif not self.current_todos:
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
        self.query_one("#no-categories", Static).set_class(
            not self.categories, "visible"
        )
        category_labels = [
            f"{index + 1}. {category.get('categoryName') or 'Category'}"
            for index, category in enumerate(self.categories)
        ]
        category_tabs = self.query(".category-tab")
        for index, category_tab in enumerate(category_tabs):
            visible = index < len(self.categories)
            category_tab.update(Text(category_labels[index]) if visible else "")
            category_tab.set_class(not visible, "hidden")
            category_tab.set_class(visible and index == self.category_index, "active")
        if self.weekly_mode:
            help_text = (
                "j/k move  a add  Space toggle  d remove  e dates  r reorder  Esc normal"
                if self.weekly_insert_mode
                else "i insert  Esc back to to-dos"
            )
        elif self.day_todos_mode:
            help_text = (
                "j/k move  a add  v view  d delete  e edit  r reorder  Esc back"
                if self.day_select_mode
                else "e choose date  i select  Esc back to to-dos"
            )
        else:
            help_text = (
                "1-9 switch  a add  d delete  r reorder categories  i select  0 weekly  Ctrl+J day  Esc quit"
                if not self.select_mode
                else "j/k move  a add  v view  d delete  e edit  r reorder  Esc back"
            )
        self.query_one("#help", Static).update(help_text)

    def _format_week_range(self) -> str:
        try:
            start = date.fromisoformat(self.weekly_data["start_date"])
            end = date.fromisoformat(self.weekly_data["end_date"])
        except KeyError, TypeError, ValueError:
            return "Weekly tasks"
        start_month = MONTH_ABBREVIATIONS[start.month - 1]
        end_month = MONTH_ABBREVIATIONS[end.month - 1]
        return f"{start.day} {start_month} - {end.day} {end_month}"

    def _format_day_date(self) -> str:
        try:
            selected = date.fromisoformat(self.day_data["date"])
        except KeyError, TypeError, ValueError:
            return "Choose a date"
        return f"{selected.day} {MONTH_ABBREVIATIONS[selected.month - 1]}"

    def _set_message(self, message: str) -> None:
        self.message = message
        if self.is_mounted:
            self.query_one("#status", Static).update(Text(message))

    def _report_error(self, message: str) -> None:
        self._set_message(f"Error: {message}")

    def action_enter_weekly(self) -> None:
        if self.select_mode or self.weekly_mode or self.day_todos_mode:
            return
        self.weekly_mode = True
        self.weekly_insert_mode = False
        self.weekly_data = load_weekly_tasks(self.weekly_path, self._report_error)
        self.weekly_index = min(
            self.weekly_index, max(0, len(self.current_weekly_items) - 1)
        )
        self.refresh_view()

    def action_enter_day_todos(self) -> None:
        if self.select_mode or self.weekly_mode or self.day_todos_mode:
            return
        self.day_todos_mode = True
        self.day_select_mode = False
        self.day_data = load_day_todos(self.day_todos_path, self._report_error)
        self.day_todo_index = min(
            self.day_todo_index, max(0, len(self.current_day_todos) - 1)
        )
        self.refresh_view()

    def action_select_category(self, index: int) -> None:
        if (
            not self.weekly_mode
            and not self.day_todos_mode
            and not self.select_mode
            and 0 <= index < len(self.categories)
        ):
            self.category_index = index
            self.todo_index = 0
            self._set_message("")
            self.refresh_view()

    def action_enter_select(self) -> None:
        if self.weekly_mode:
            self.weekly_insert_mode = True
            self.weekly_index = min(
                self.weekly_index, max(0, len(self.current_weekly_items) - 1)
            )
            self._set_message("Insert mode")
            self.refresh_view()
            return
        if self.day_todos_mode:
            self.day_select_mode = True
            self.day_todo_index = min(
                self.day_todo_index, max(0, len(self.current_day_todos) - 1)
            )
            self._set_message("Select a to-do")
            self.refresh_view()
            return
        if self.current_category:
            self.select_mode = True
            self.todo_index = min(self.todo_index, max(0, len(self.current_todos) - 1))
            self._set_message("Select a to-do")
            self.refresh_view()

    def action_back(self) -> None:
        if self.weekly_mode:
            if self.weekly_insert_mode:
                self.weekly_insert_mode = False
                self._set_message("Normal mode")
            else:
                self.weekly_mode = False
                self._set_message("Back to to-dos")
            self.refresh_view()
            return
        if self.day_todos_mode:
            if self.day_select_mode:
                self.day_select_mode = False
                self._set_message("Normal mode")
            else:
                self.day_todos_mode = False
                self._set_message("Back to to-dos")
            self.refresh_view()
            return
        if self.select_mode:
            self.select_mode = False
            self._set_message("Normal mode")
            self.refresh_view()
        else:
            self.exit()

    def action_move_down(self) -> None:
        if self.weekly_mode and self.weekly_insert_mode and self.current_weekly_items:
            self.weekly_index = min(
                len(self.current_weekly_items) - 1, self.weekly_index + 1
            )
            self.refresh_view()
            return
        if self.day_todos_mode and self.day_select_mode and self.current_day_todos:
            self.day_todo_index = min(
                len(self.current_day_todos) - 1, self.day_todo_index + 1
            )
            self.refresh_view()
            return
        if self.select_mode and self.current_todos:
            self.todo_index = min(len(self.current_todos) - 1, self.todo_index + 1)
            self.refresh_view()

    def action_move_up(self) -> None:
        if self.weekly_mode and self.weekly_insert_mode and self.current_weekly_items:
            self.weekly_index = max(0, self.weekly_index - 1)
            self.refresh_view()
            return
        if self.day_todos_mode and self.day_select_mode and self.current_day_todos:
            self.day_todo_index = max(0, self.day_todo_index - 1)
            self.refresh_view()
            return
        if self.select_mode and self.current_todos:
            self.todo_index = max(0, self.todo_index - 1)
            self.refresh_view()

    def action_add_todo(self) -> None:
        if self.weekly_mode:
            if not self.weekly_insert_mode:
                return
            self.push_screen(
                FormDialog("Add weekly task", [("Name", "", False)]),
                self._added_weekly_task,
            )
            return
        if self.day_todos_mode:
            if not self.day_select_mode:
                return
            self.push_screen(
                FormDialog(
                    "Add a to-do for this date",
                    [("Title", "", False), ("Details", "", True)],
                ),
                self._added_day_todo,
            )
            return
        if not self.select_mode:
            if len(self.categories) >= 9:
                self._set_message("Maximum of 9 categories reached")
                return
            self.push_screen(
                FormDialog("Add a category", [("Name", "", False)]),
                self._added_category,
            )
            return
        if not self.current_category:
            return
        self.push_screen(
            FormDialog(
                "Add a to-do",
                [("Title", "", False), ("Details", "", True)],
            ),
            self._added_todo,
        )

    def _added_category(self, values: list[str] | None) -> None:
        if values is None:
            return
        name = values[0].strip()
        if not name:
            self._set_message("Category name cannot be empty")
            return
        self.message = ""
        if add_category(name, self.path, self._report_error):
            self._load_data()
            self.category_index = max(0, len(self.categories) - 1)
            self.todo_index = 0
            self._set_message("Category added")
        else:
            self._set_message(self.message or "Add category failed")
        self.refresh_view()

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
            category["id"],
            self.path,
            {"title": title, "details": details or None},
            self._report_error,
        ):
            self._load_data()
            self.todo_index = max(0, len(self.current_todos) - 1)
            self._set_message("To-do added")
            self.refresh_view()
        elif not self.message:
            self._set_message("Add failed")

    def action_view_todo(self) -> None:
        if self.day_todos_mode:
            todo = self.current_day_todo
            if not self.day_select_mode or not todo:
                return
            self.push_screen(
                InfoDialog(
                    str(todo.get("title", "")),
                    "",
                    body=str(todo.get("details") or "(No details)"),
                    confirm_label="Close",
                )
            )
            return
        todo = self.current_todo
        if self.weekly_mode or not self.select_mode or not todo:
            return
        title = str(todo.get("title", ""))
        details = str(todo.get("details") or "(No details)")
        self.push_screen(InfoDialog(title, "", body=details, confirm_label="Close"))

    def action_delete_todo(self) -> None:
        if self.weekly_mode:
            task = self.current_weekly_task
            if not self.weekly_insert_mode or not task:
                return
            self.push_screen(
                InfoDialog(
                    f"Delete {task['name']}?",
                    "Are you sure you want to delete this weekly task?",
                    confirm_label="Delete",
                    destructive=True,
                ),
                lambda confirmed: self._deleted_weekly_task(confirmed, task),
            )
            return
        if self.day_todos_mode:
            todo = self.current_day_todo
            if not self.day_select_mode or not todo:
                return
            self.push_screen(
                InfoDialog(
                    f"Delete {todo.get('title', 'to-do')}?",
                    "Are you sure you want to delete this to-do?",
                    confirm_label="Delete",
                    destructive=True,
                ),
                lambda confirmed: self._deleted_day_todo(confirmed, todo),
            )
            return
        if not self.select_mode:
            category = self.current_category
            if not category:
                return
            todo_count = len(category.get("toDos", []))
            detail = (
                f" Its {todo_count} to-dos will also be deleted." if todo_count else ""
            )
            self.push_screen(
                InfoDialog(
                    f"Delete {category.get('categoryName', 'category')}?",
                    "Are you sure you want to delete this category?" + detail,
                    confirm_label="Delete",
                    destructive=True,
                ),
                lambda confirmed: self._deleted_category(confirmed, category),
            )
            return
        todo, category = self.current_todo, self.current_category
        if not todo or not category:
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

    def _deleted_category(
        self, confirmed: bool | None, category: dict[str, Any]
    ) -> None:
        if not confirmed:
            return
        self.message = ""
        old_index = self.category_index
        if delete_category(category["id"], self.path, self._report_error):
            self._load_data()
            self.category_index = min(old_index, max(0, len(self.categories) - 1))
            self.todo_index = 0
            self._set_message("Category deleted")
        else:
            self._set_message(self.message or "Delete category failed")
        self.refresh_view()

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
        if self.weekly_mode:
            if not self.weekly_insert_mode:
                return
            self.push_screen(
                FormDialog(
                    "Edit date range",
                    [
                        (
                            "Start date (YYYY-MM-DD)",
                            self.weekly_data["start_date"],
                            False,
                        ),
                        ("End date (YYYY-MM-DD)", self.weekly_data["end_date"], False),
                    ],
                ),
                self._edited_week_dates,
            )
            return
        if self.day_todos_mode:
            if not self.day_select_mode:
                self.push_screen(
                    DatePickerDialog(
                        self.day_data.get("date", date.today().isoformat())
                    ),
                    self._edited_day_date,
                )
                return
            todo = self.current_day_todo
            if not todo:
                return
            self.push_screen(
                FormDialog(
                    "Edit to-do",
                    [
                        ("Title", str(todo.get("title", "")), False),
                        ("Details", str(todo.get("details") or ""), True),
                    ],
                ),
                lambda values: self._edited_day_todo(values, todo),
            )
            return
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
        if self.weekly_mode:
            task = self.current_weekly_task
            if not self.weekly_insert_mode or not task:
                return
            self.push_screen(
                FormDialog(
                    "Reorder weekly task",
                    [
                        (
                            f"Position (1-{len(self.current_weekly_items)})",
                            str(self.weekly_index + 1),
                            False,
                        )
                    ],
                ),
                lambda values: self._rearranged_weekly_task(values, task),
            )
            return
        if self.day_todos_mode:
            todo = self.current_day_todo
            if not self.day_select_mode or not todo:
                return
            self.push_screen(
                FormDialog(
                    "Reorder to-do",
                    [
                        (
                            f"Position (1-{len(self.current_day_todos)})",
                            str(self.day_todo_index + 1),
                            False,
                        )
                    ],
                ),
                lambda values: self._rearranged_day_todo(values, todo),
            )
            return
        if not self.select_mode:
            category = self.current_category
            if not category:
                return
            self.push_screen(
                FormDialog(
                    "Reorder category",
                    [
                        (
                            f"Position (1-{len(self.categories)})",
                            str(self.category_index + 1),
                            False,
                        )
                    ],
                ),
                self._rearranged_category,
            )
            return
        todo = self.current_todo
        if not todo:
            return
        self.push_screen(
            FormDialog(
                "Reorder to-do",
                [
                    (
                        f"Position (1-{len(self.current_todos)})",
                        str(self.todo_index + 1),
                        False,
                    )
                ],
            ),
            lambda values: self._rearranged_todo(values, todo),
        )

    def _rearranged_category(self, values: list[str] | None) -> None:
        if values is None:
            return
        try:
            place = int(values[0])
        except ValueError:
            self._set_message("Enter a whole number")
            return
        category = self.current_category
        self.message = ""
        if category and rearrange_categories(
            self.path, category["id"], place, self._report_error
        ):
            self._load_data()
            self.category_index = place - 1
            self.todo_index = 0
            self._set_message("Category moved")
        else:
            self._set_message(self.message or "Reorder failed")
        self.refresh_view()

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

    def _rearranged_weekly_task(
        self, values: list[str] | None, task: dict[str, Any]
    ) -> None:
        if values is None:
            return
        try:
            place = int(values[0])
        except ValueError:
            self._set_message("Enter a whole number")
            return
        self.message = ""
        if rearrange_weekly_task(
            self.weekly_path, task["id"], place, self._report_error
        ):
            self.weekly_data = load_weekly_tasks(self.weekly_path, self._report_error)
            self.weekly_index = place - 1
            self._set_message("Weekly task moved")
        else:
            self._set_message(self.message or "Reorder failed")
        self.refresh_view()

    def action_toggle_weekly_task(self) -> None:
        task = self.current_weekly_task
        if not self.weekly_mode or not self.weekly_insert_mode or not task:
            return
        self.message = ""
        if toggle_weekly_task(self.weekly_path, task["id"], self._report_error):
            self.weekly_data = load_weekly_tasks(self.weekly_path, self._report_error)
            self._set_message(
                "Task marked done"
                if task.get("done") is False
                else "Task marked not done"
            )
        else:
            self._set_message(self.message or "Could not update task")
        self.refresh_view()

    def _added_weekly_task(self, values: list[str] | None) -> None:
        if values is None:
            return
        self.message = ""
        if add_weekly_task(self.weekly_path, values[0], self._report_error):
            self.weekly_data = load_weekly_tasks(self.weekly_path, self._report_error)
            self.weekly_index = max(0, len(self.current_weekly_items) - 1)
            self._set_message("Weekly task added")
        else:
            self._set_message(self.message or "Add failed")
        self.refresh_view()

    def _deleted_weekly_task(
        self, confirmed: bool | None, task: dict[str, Any]
    ) -> None:
        if not confirmed:
            return
        self.message = ""
        if delete_weekly_task(self.weekly_path, task["id"], self._report_error):
            self.weekly_data = load_weekly_tasks(self.weekly_path, self._report_error)
            self.weekly_index = min(
                self.weekly_index, max(0, len(self.current_weekly_items) - 1)
            )
            self._set_message("Weekly task removed")
        else:
            self._set_message(self.message or "Delete failed")
        self.refresh_view()

    def _edited_week_dates(self, values: list[str] | None) -> None:
        if values is None:
            return
        self.message = ""
        if set_weekly_dates(
            self.weekly_path, values[0].strip(), values[1].strip(), self._report_error
        ):
            self.weekly_data = load_weekly_tasks(self.weekly_path, self._report_error)
            self._set_message("Date range saved")
        else:
            self._set_message(self.message or "Date range was not saved")
        self.refresh_view()

    def _added_day_todo(self, values: list[str] | None) -> None:
        if values is None:
            return
        self.message = ""
        if add_day_todo(self.day_todos_path, values[0], values[1], self._report_error):
            self.day_data = load_day_todos(self.day_todos_path, self._report_error)
            self.day_todo_index = max(0, len(self.current_day_todos) - 1)
            self._set_message("To-do added")
        else:
            self._set_message(self.message or "Add failed")
        self.refresh_view()

    def _deleted_day_todo(self, confirmed: bool | None, todo: dict[str, Any]) -> None:
        if not confirmed:
            return
        self.message = ""
        if delete_day_todo(self.day_todos_path, todo["id"], self._report_error):
            self.day_data = load_day_todos(self.day_todos_path, self._report_error)
            self.day_todo_index = min(
                self.day_todo_index, max(0, len(self.current_day_todos) - 1)
            )
            self._set_message("To-do deleted")
        else:
            self._set_message(self.message or "Delete failed")
        self.refresh_view()

    def _edited_day_todo(self, values: list[str] | None, todo: dict[str, Any]) -> None:
        if values is None:
            return
        self.message = ""
        if edit_day_todo(
            self.day_todos_path,
            todo["id"],
            values[0],
            values[1],
            self._report_error,
        ):
            self.day_data = load_day_todos(self.day_todos_path, self._report_error)
            self._set_message("To-do saved")
        else:
            self._set_message(self.message or "Edit failed")
        self.refresh_view()

    def _rearranged_day_todo(
        self, values: list[str] | None, todo: dict[str, Any]
    ) -> None:
        if values is None:
            return
        try:
            place = int(values[0])
        except ValueError:
            self._set_message("Enter a whole number")
            return
        self.message = ""
        if rearrange_day_todo(
            self.day_todos_path, todo["id"], place, self._report_error
        ):
            self.day_data = load_day_todos(self.day_todos_path, self._report_error)
            self.day_todo_index = place - 1
            self._set_message("To-do moved")
        else:
            self._set_message(self.message or "Reorder failed")
        self.refresh_view()

    def _edited_day_date(self, selected_date: str | None) -> None:
        if selected_date is None:
            return
        self.message = ""
        if set_day_date(self.day_todos_path, selected_date, self._report_error):
            self.day_data = load_day_todos(self.day_todos_path, self._report_error)
            self._set_message("Date saved")
        else:
            self._set_message(self.message or "Date was not saved")
        self.refresh_view()


class DatePickerDialog(ModalScreen[str | None]):
    """Keyboard-operated monthly calendar for selecting one date."""

    BINDINGS = [
        Binding("escape", "cancel", show=False, priority=True),
        Binding("enter", "choose", show=False, priority=True),
        Binding("h", "previous_day", show=False, priority=True),
        Binding("l", "next_day", show=False, priority=True),
        Binding("k", "previous_week", show=False, priority=True),
        Binding("j", "next_week", show=False, priority=True),
        Binding("H", "previous_month", show=False, priority=True),
        Binding("L", "next_month", show=False, priority=True),
        Binding("S", "today", show=False, priority=True),
    ]
    CSS = """
    DatePickerDialog {
        align: center middle;
        background: #101010 85%;
    }
    #date-dialog {
        width: 46;
        height: auto;
        border: round #777777;
        background: #242424;
        padding: 1 2;
    }
    #date-title {
        height: 1;
        margin-bottom: 1;
        text-style: bold;
    }
    #date-month {
        height: 1;
        text-style: bold;
        content-align: center middle;
    }
    #date-calendar {
        height: 7;
        content-align: center middle;
    }
    #date-help {
        height: 3;
        margin-top: 1;
        color: #a0a0a0;
        content-align: center middle;
    }
    """

    def __init__(self, selected_date: str):
        super().__init__()
        try:
            self.selected_date = date.fromisoformat(selected_date)
        except ValueError:
            self.selected_date = date.today()

    def compose(self) -> ComposeResult:
        with Vertical(id="date-dialog"):
            yield Static("Choose a date", id="date-title")
            yield Static("", id="date-month")
            yield Static("", id="date-calendar", markup=False)
            yield Static(
                "h/l day  k/j week  H/L month\nS today  Enter choose  Esc cancel",
                id="date-help",
                markup=False,
            )

    def on_mount(self) -> None:
        self.refresh_calendar()

    def refresh_calendar(self) -> None:
        self.query_one("#date-month", Static).update(
            f"{MONTH_ABBREVIATIONS[self.selected_date.month - 1]} {self.selected_date.year}"
        )
        calendar_text = Text("Mo Tu We Th Fr Sa Su\n")
        weeks = calendar.monthcalendar(
            self.selected_date.year, self.selected_date.month
        )
        today = date.today()
        for week_index, week in enumerate(weeks):
            for day_number in week:
                if day_number == 0:
                    calendar_text.append("   ")
                    continue
                current = date(
                    self.selected_date.year, self.selected_date.month, day_number
                )
                label = f"{day_number:2} "
                style = None
                if current == self.selected_date:
                    label = f"{day_number:2} "
                    style = "bold black on #d8d8d8"
                elif current == today:
                    style = "underline"
                calendar_text.append(label, style=style)
            if week_index < len(weeks) - 1:
                calendar_text.append("\n")
        self.query_one("#date-calendar", Static).update(calendar_text)

    def _change_month(self, amount: int) -> None:
        month_index = (
            self.selected_date.year * 12 + self.selected_date.month - 1 + amount
        )
        year, zero_based_month = divmod(month_index, 12)
        month = zero_based_month + 1
        day_number = min(self.selected_date.day, calendar.monthrange(year, month)[1])
        self.selected_date = date(year, month, day_number)
        self.refresh_calendar()

    def action_previous_day(self) -> None:
        self.selected_date = date.fromordinal(self.selected_date.toordinal() - 1)
        self.refresh_calendar()

    def action_next_day(self) -> None:
        self.selected_date = date.fromordinal(self.selected_date.toordinal() + 1)
        self.refresh_calendar()

    def action_previous_week(self) -> None:
        self.selected_date = date.fromordinal(self.selected_date.toordinal() - 7)
        self.refresh_calendar()

    def action_next_week(self) -> None:
        self.selected_date = date.fromordinal(self.selected_date.toordinal() + 7)
        self.refresh_calendar()

    def action_previous_month(self) -> None:
        self._change_month(-1)

    def action_next_month(self) -> None:
        self._change_month(1)

    def action_today(self) -> None:
        self.selected_date = date.today()
        self.refresh_calendar()

    def action_choose(self) -> None:
        self.dismiss(self.selected_date.isoformat())

    def action_cancel(self) -> None:
        self.dismiss(None)


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
                (
                    "Enter close  ·  Esc cancel"
                    if self.confirm_label == "Close"
                    else "Enter confirm  ·  Esc cancel"
                ),
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
        Binding("ctrl+l", "previous_field", show=False, priority=True),
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
                    yield TextArea(
                        value, id=f"field-{index}", classes="field-text-area"
                    )
                else:
                    yield Input(value, id=f"field-{index}", classes="field-input")
            yield Static(
                "Ctrl+N: next field  ·  Ctrl+L: previous field  ·  Esc: cancel",
                id="instructions",
            )

    def on_mount(self) -> None:
        self.query_one("#field-0").focus()

    def action_next_field(self) -> None:
        if self.ready_to_save:
            return
        if self.field_stage + 1 < len(self.fields):
            self.field_stage += 1
            self.query_one(f"#field-{self.field_stage}").focus()
            instruction = (
                "Ctrl+N: finish fields  ·  Ctrl+L: previous field  ·  Esc: cancel"
            )
        else:
            self.ready_to_save = True
            instruction = "Ctrl+S: save  ·  Ctrl+L: previous field  ·  Esc: cancel"
        self.query_one("#instructions", Static).update(instruction)

    def action_previous_field(self) -> None:
        if self.ready_to_save:
            self.ready_to_save = False
            self.field_stage = len(self.fields) - 1
        elif self.field_stage > 0:
            self.field_stage -= 1
        else:
            return
        self.query_one(f"#field-{self.field_stage}").focus()
        self.query_one("#instructions", Static).update(
            "Ctrl+N: next field  ·  Ctrl+L: previous field  ·  Esc: cancel"
        )

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
