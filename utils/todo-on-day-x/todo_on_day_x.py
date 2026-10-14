"""JSON helpers for the date-specific to-do list used by the Textual interface."""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "todo-on-day-x.json"
ErrorCallback = Callable[[str], None] | None


def _default_data() -> dict[str, Any]:
    return {"date": date.today().isoformat(), "toDos": []}


def _path(path: str | Path | None) -> Path:
    return Path(path) if path is not None else DEFAULT_PATH


def _report(on_error: ErrorCallback, message: str) -> None:
    if on_error:
        on_error(message)


def _valid_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _validate_data(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict) or not _valid_date(data.get("date")):
        return None
    todos = data.get("toDos")
    if not isinstance(todos, list):
        return None

    valid_todos: list[dict[str, Any]] = []
    for todo in todos:
        if not isinstance(todo, dict):
            return None
        todo_id = todo.get("id")
        title = todo.get("title")
        details = todo.get("details")
        if (
            not isinstance(todo_id, str)
            or not isinstance(title, str)
            or (details is not None and not isinstance(details, str))
        ):
            return None
        valid_todos.append({"id": todo_id, "title": title, "details": details})
    return {"date": data["date"], "toDos": valid_todos}


def _write(path: Path, data: dict[str, Any], on_error: ErrorCallback) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
            file.write("\n")
        return True
    except OSError as exc:
        _report(on_error, str(exc))
        return False


def _read(path: str | Path | None, on_error: ErrorCallback) -> dict[str, Any] | None:
    data_path = _path(path)
    try:
        with data_path.open(encoding="utf-8") as file:
            raw_data = json.load(file)
    except FileNotFoundError:
        initial_data = _default_data()
        if _write(data_path, initial_data, on_error):
            return initial_data
        return None
    except (OSError, json.JSONDecodeError) as exc:
        _report(on_error, str(exc))
        return None

    data = _validate_data(raw_data)
    if data is None:
        _report(on_error, "todo-on-day-x.json has an invalid structure or date")
    return data


def load_day_todos(
    path: str | Path | None = None,
    on_error: ErrorCallback = None,
) -> dict[str, Any]:
    """Load the selected date and its to-dos, creating the file if absent."""
    return _read(path, on_error) or _default_data()


def set_day_date(
    path: str | Path | None,
    selected_date: str,
    on_error: ErrorCallback = None,
) -> bool:
    """Change the displayed date without changing the stored to-dos."""
    if not _valid_date(selected_date):
        _report(on_error, "Choose a valid date")
        return False
    data = _read(path, on_error)
    if data is None:
        return False
    data["date"] = selected_date
    return _write(_path(path), data, on_error)


def add_day_todo(
    path: str | Path | None,
    title: str,
    details: str = "",
    on_error: ErrorCallback = None,
) -> bool:
    """Append a to-do to the selected day."""
    clean_title = title.strip()
    if not clean_title:
        _report(on_error, "Title cannot be empty")
        return False
    data = _read(path, on_error)
    if data is None:
        return False
    data["toDos"].append(
        {
            "id": uuid.uuid4().hex[:8],
            "title": clean_title,
            "details": details or None,
        }
    )
    return _write(_path(path), data, on_error)


def edit_day_todo(
    path: str | Path | None,
    todo_id: str,
    title: str,
    details: str,
    on_error: ErrorCallback = None,
) -> bool:
    """Update one to-do's title and details."""
    clean_title = title.strip()
    if not clean_title:
        _report(on_error, "Title cannot be empty")
        return False
    data = _read(path, on_error)
    if data is None:
        return False
    for todo in data["toDos"]:
        if todo["id"] == todo_id:
            todo["title"] = clean_title
            todo["details"] = details or None
            return _write(_path(path), data, on_error)
    _report(on_error, f"No to-do with id: {todo_id}")
    return False


def delete_day_todo(
    path: str | Path | None,
    todo_id: str,
    on_error: ErrorCallback = None,
) -> bool:
    """Remove one to-do by its stable id."""
    data = _read(path, on_error)
    if data is None:
        return False
    for index, todo in enumerate(data["toDos"]):
        if todo["id"] == todo_id:
            del data["toDos"][index]
            return _write(_path(path), data, on_error)
    _report(on_error, f"No to-do with id: {todo_id}")
    return False


def rearrange_day_todo(
    path: str | Path | None,
    todo_id: str,
    new_place: int,
    on_error: ErrorCallback = None,
) -> bool:
    """Move a to-do to a one-based position in the stored order."""
    data = _read(path, on_error)
    if data is None:
        return False
    todos = data["toDos"]
    if new_place < 1 or new_place > len(todos):
        _report(on_error, f"Position must be between 1 and {len(todos)}")
        return False
    todo_index = next(
        (index for index, todo in enumerate(todos) if todo["id"] == todo_id),
        None,
    )
    if todo_index is None:
        _report(on_error, f"No to-do with id: {todo_id}")
        return False
    todo = todos.pop(todo_index)
    todos.insert(new_place - 1, todo)
    return _write(_path(path), data, on_error)
