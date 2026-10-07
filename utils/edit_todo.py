import json
from collections.abc import Callable
from pathlib import Path


def edit_todo(
    category_id: str,
    path_to_json: Path,
    todo_id: str,
    editTitle: str | None = None,
    editDetails: str | None = None,
    on_error: Callable[[str], None] | None = None,
) -> bool | None:
    try:
        with open(path_to_json, "r") as file:
            json_data: list[dict] = json.load(file)
    except (FileNotFoundError, PermissionError, OSError) as e:
        if on_error:
            on_error(str(e))
        return False

    is_category_found = False
    is_todo_id_found = False

    for item in json_data:
        if item["id"] == category_id:
            is_category_found = True
            for todo in item["toDos"]:
                if todo["id"] == todo_id:
                    is_todo_id_found = True
                    if editTitle:
                        todo["title"] = editTitle
                    if editDetails is None:
                        pass
                    elif not editDetails:
                        todo["details"] = None
                    else:
                        todo["details"] = editDetails

    if not is_category_found:
        if on_error:
            on_error("Category not found")
        return False
    if not is_todo_id_found:
        if on_error:
            on_error("Todo id not found")
        return False

    try:
        with open(path_to_json, "w") as file:
            json.dump(json_data, file, indent=2)
            return True
    except (FileNotFoundError, PermissionError, OSError) as e:
        if on_error:
            on_error(str(e))
        return False


if __name__ == "__main__":
    path = Path(__file__).parent.parent / "data" / "to-do-test.json"
    edit_todo(
        "computer-systems",
        path,
        "c171bf76",
        editDetails="Learn about inner stuff of CPUS",
    )
