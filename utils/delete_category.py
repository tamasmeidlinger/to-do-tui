import json
from collections.abc import Callable
from pathlib import Path


MAX_CATEGORIES = 9


def delete_category(
    category_id: str,
    path_to_json: Path,
    on_error: Callable[[str], None] | None = None,
) -> bool:
    try:
        with path_to_json.open("r", encoding="utf-8") as file:
            json_data = json.load(file)
        if not isinstance(json_data, list):
            raise ValueError("Expected a list of categories")
    except (FileNotFoundError, PermissionError, OSError, json.JSONDecodeError, ValueError) as exc:
        if on_error:
            on_error(str(exc))
        return False

    category_index = next(
        (
            index
            for index, category in enumerate(json_data[:MAX_CATEGORIES])
            if isinstance(category, dict) and category.get("id") == category_id
        ),
        None,
    )
    if category_index is None:
        if on_error:
            on_error("Category not found")
        return False

    del json_data[category_index]
    try:
        with path_to_json.open("w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=2)
        return True
    except (FileNotFoundError, PermissionError, OSError) as exc:
        if on_error:
            on_error(str(exc))
        return False
