"""JSON helpers for the weekly task list used by the Textual interface."""

from __future__ import annotations

import json
import uuid
from datetime import date, timedelta
from pathlib import Path
from collections.abc import Callable
from typing import Any


DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "weekly-tasks.json"
ErrorCallback = Callable[[str], None] | None


def _default_data() -> dict[str, Any]:
    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "items": [],
    }


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
    if not isinstance(data, dict):
        return None
    start = data.get("start_date")
    end = data.get("end_date")
    items = data.get("items")
    if not _valid_date(start) or not _valid_date(end):
        return None
    if date.fromisoformat(end) < date.fromisoformat(start) or not isinstance(items, list):
        return None

    valid_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            return None
        task_id = item.get("id")
        name = item.get("name")
        done = item.get("done")
        if not isinstance(task_id, str) or not isinstance(name, str) or not isinstance(done, bool):
            return None
        valid_items.append({"id": task_id, "name": name, "done": done})
    return {"start_date": start, "end_date": end, "items": valid_items}


def _write(data_path: Path, data: dict[str, Any], on_error: ErrorCallback) -> bool:
    try:
        data_path.parent.mkdir(parents=True, exist_ok=True)
        with data_path.open("w", encoding="utf-8") as file:
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
        _report(on_error, "weekly-tasks.json has an invalid structure or date")
    return data


def load_weekly_tasks(
    path: str | Path | None = None,
    on_error: ErrorCallback = None,
) -> dict[str, Any]:
    """Load the current range and tasks, creating the file with this week if absent."""
    return _read(path, on_error) or _default_data()


def set_weekly_dates(
    path: str | Path | None,
    start_date: str,
    end_date: str,
    on_error: ErrorCallback = None,
) -> bool:
    """Change the displayed date range without changing task completion states."""
    if not _valid_date(start_date) or not _valid_date(end_date):
        _report(on_error, "Use dates in YYYY-MM-DD format")
        return False
    if date.fromisoformat(end_date) < date.fromisoformat(start_date):
        _report(on_error, "The end date must be on or after the start date")
        return False
    data = _read(path, on_error)
    if data is None:
        return False
    data["start_date"] = start_date
    data["end_date"] = end_date
    return _write(_path(path), data, on_error)


def add_weekly_task(
    path: str | Path | None,
    name: str,
    on_error: ErrorCallback = None,
) -> bool:
    """Append a new unchecked task."""
    clean_name = name.strip()
    if not clean_name:
        _report(on_error, "Task name cannot be empty")
        return False
    data = _read(path, on_error)
    if data is None:
        return False
    data["items"].append({"id": uuid.uuid4().hex[:8], "name": clean_name, "done": False})
    return _write(_path(path), data, on_error)


def toggle_weekly_task(
    path: str | Path | None,
    task_id: str,
    on_error: ErrorCallback = None,
) -> bool:
    """Flip one task's done state."""
    data = _read(path, on_error)
    if data is None:
        return False
    for item in data["items"]:
        if item["id"] == task_id:
            item["done"] = not item["done"]
            return _write(_path(path), data, on_error)
    _report(on_error, f"No weekly task with id: {task_id}")
    return False


def delete_weekly_task(
    path: str | Path | None,
    task_id: str,
    on_error: ErrorCallback = None,
) -> bool:
    """Remove one task by its stable id."""
    data = _read(path, on_error)
    if data is None:
        return False
    for index, item in enumerate(data["items"]):
        if item["id"] == task_id:
            del data["items"][index]
            return _write(_path(path), data, on_error)
    _report(on_error, f"No weekly task with id: {task_id}")
    return False


def rearrange_weekly_task(
    path: str | Path | None,
    task_id: str,
    new_place: int,
    on_error: ErrorCallback = None,
) -> bool:
    """Move a task to a one-based position in the stored item order."""
    data = _read(path, on_error)
    if data is None:
        return False
    items = data["items"]
    if new_place < 1 or new_place > len(items):
        _report(on_error, f"Position must be between 1 and {len(items)}")
        return False

    task_index = next(
        (index for index, item in enumerate(items) if item["id"] == task_id),
        None,
    )
    if task_index is None:
        _report(on_error, f"No weekly task with id: {task_id}")
        return False

    task = items.pop(task_index)
    items.insert(new_place - 1, task)
    return _write(_path(path), data, on_error)
