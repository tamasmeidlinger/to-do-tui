import json
from pathlib import Path
from collections.abc import Callable


def list_todos(
    category_id: str,
    path_to_json: Path,
    on_error: Callable[[str], None] | None = None,
) -> bool | None:
    try:
        with open(path_to_json, "r") as file:
            json_data = json.load(file)
            for item in json_data:
                if item["id"] == category_id:
                    return True
                continue
            return False
    except (FileNotFoundError, PermissionError, OSError, json.JSONDecodeError) as e:
        if on_error:
            on_error(str(e))
        return False
