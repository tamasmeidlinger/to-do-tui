import json
import re
from collections.abc import Callable
from pathlib import Path


MAX_CATEGORIES = 9


def add_category(
    category_name: str,
    path_to_json: Path,
    on_error: Callable[[str], None] | None = None,
) -> bool:
    name = category_name.strip()
    if not name:
        if on_error:
            on_error("Category name cannot be empty")
        return False

    try:
        with path_to_json.open("r", encoding="utf-8") as file:
            json_data = json.load(file)
        if not isinstance(json_data, list):
            raise ValueError("Expected a list of categories")
    except (FileNotFoundError, PermissionError, OSError, json.JSONDecodeError, ValueError) as exc:
        if on_error:
            on_error(str(exc))
        return False

    if len(json_data[:MAX_CATEGORIES]) >= MAX_CATEGORIES:
        if on_error:
            on_error(f"Maximum of {MAX_CATEGORIES} categories reached")
        return False

    category_id = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")
    if not category_id:
        if on_error:
            on_error("Category name must contain letters or numbers")
        return False

    if any(
        isinstance(category, dict) and category.get("id") == category_id
        for category in json_data
    ):
        if on_error:
            on_error(f"A category with the id '{category_id}' already exists")
        return False

    json_data.append(
        {
            "id": category_id,
            "categoryName": name,
            "toDos": [],
        }
    )
    try:
        with path_to_json.open("w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=2)
        return True
    except (FileNotFoundError, PermissionError, OSError) as exc:
        if on_error:
            on_error(str(exc))
        return False
