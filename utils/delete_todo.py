import json
from pathlib import Path
from collections.abc import Callable


def delete_todo(
    category_id: str,
    path_to_json: Path,
    todo_id: str,
    on_error: Callable[[str], None] | None = None,
) -> bool:
    try:
        with open(path_to_json, "r") as file:
            json_data: list[dict] = json.load(file)
    except (FileNotFoundError, PermissionError, OSError) as e:
        if on_error:
            on_error(str(e))
        return False

    item_to_remove = None

    for item in json_data:
        if item["id"] == category_id:
            for index, todo in enumerate(item["toDos"]):
                if todo["id"] == todo_id:
                    item_to_remove = todo
                    item["toDos"].pop(index)
                    break
                continue
            if not item_to_remove:
                if on_error:
                    on_error(f"No item with id: {todo_id}")
                return False

            try:
                with open(path_to_json, "w") as file:
                    json.dump(json_data, file, indent=2)
                    return True
            except (FileNotFoundError, PermissionError, OSError) as e:
                if on_error:
                    on_error(str(e))
                return False
        continue
    if on_error:
        on_error("Category not found")
    return False
