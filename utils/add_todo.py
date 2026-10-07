import json
import uuid
from pathlib import Path
from collections.abc import Callable


def add_todo(
    category_id: str,
    path_to_json: Path,
    to_add: dict,
    on_error: Callable[[str], None] | None = None,
) -> bool:
    try:
        with open(path_to_json, "r") as file:
            json_data: list[dict] = json.load(file)
    except (FileNotFoundError, PermissionError, OSError) as e:
        if on_error:
            on_error(str(e))
        return False

    for item in json_data:
        if item["id"] == category_id:
            to_add = {"id": uuid.uuid1().hex[:8], **to_add}
            item["toDos"].append(to_add)
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
