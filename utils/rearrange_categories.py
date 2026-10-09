import json
from collections.abc import Callable
from pathlib import Path


MAX_CATEGORIES = 9


def rearrange_categories(
    path_to_json: Path,
    category_id: str,
    new_place: int,
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

    visible_categories = json_data[:MAX_CATEGORIES]
    if not 1 <= new_place <= len(visible_categories):
        if on_error:
            on_error(f"Position must be between 1 and {len(visible_categories)}")
        return False

    category = next(
        (
            item
            for item in visible_categories
            if isinstance(item, dict) and item.get("id") == category_id
        ),
        None,
    )
    if category is None:
        if on_error:
            on_error("Category not found")
        return False

    visible_categories.remove(category)
    visible_categories.insert(new_place - 1, category)
    json_data = visible_categories + json_data[MAX_CATEGORIES:]

    try:
        with path_to_json.open("w", encoding="utf-8") as file:
            json.dump(json_data, file, indent=2)
        return True
    except (FileNotFoundError, PermissionError, OSError) as exc:
        if on_error:
            on_error(str(exc))
        return False
