import json
from pathlib import Path


def delete_todo(category_id: str, path_to_json: Path, todo_id: str) -> bool:
    try:
        with open(path_to_json, "r") as file:
            json_data: list[dict] = json.load(file)
    except (FileNotFoundError, PermissionError, OSError) as e:
        print(f"Error: {e}")
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
                print(f"No item with id: {todo_id}")
                return False

            try:
                with open(path_to_json, "w") as file:
                    json.dump(json_data, file, indent=2)
                    print(f"Removed item: {item_to_remove}")
                    return True
            except (FileNotFoundError, PermissionError, OSError) as e:
                print(f"Error message: {e}")
                return False
        continue
    print("Category not found")
    return False
