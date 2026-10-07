import json
from pathlib import Path


def edit_todo(
    category_id: str,
    path_to_json: Path,
    todo_id: str,
    editTitle: str | None = None,
    editDetails: str | None = None,
) -> bool | None:
    try:
        with open(path_to_json, "r") as file:
            json_data: list[dict] = json.load(file)
    except (FileNotFoundError, PermissionError, OSError) as e:
        print(f"Error: {e}")
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
                    print(todo)

    if not is_category_found:
        print("Category not found")
        return False
    if not is_todo_id_found:
        print("Todo id not found")
        return False

    with open(path_to_json, "w") as file:
        try:
            json.dump(json_data, file, indent=2)
            print("Edit successful")
            return True
        except (FileNotFoundError, PermissionError, OSError) as e:
            print(f"Error: {e}")
            return False


if __name__ == "__main__":
    PATH = Path(__file__).parent.parent / "data" / "to-do-test.json"
    print(PATH)
    edit_todo(
        "computer-systems",
        PATH,
        "c171bf76",
        editDetails="Learn about inner stuff of CPUS",
    )
