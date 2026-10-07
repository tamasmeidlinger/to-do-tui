import json
from pathlib import Path


def rearrange_todos(
    category_id: str, path_to_json: Path, to_do_id: str, new_place: int
) -> bool | None:
    try:
        with open(path_to_json, "r") as file:
            json_data = json.load(file)
    except (FileNotFoundError, PermissionError, OSError, json.JSONDecodeError) as e:
        print(f"Error: {e}")
        return False

    to_dos_list = None

    for item in json_data:
        if item["id"] == category_id:
            to_dos_list = item["toDos"]
            break
        continue

    if not to_dos_list:
        print("Category not found")
        return False

    if len(to_dos_list) < new_place:
        print(
            f"Cannot make that item number: {new_place}, max_number is {len(to_dos_list)}"
        )
        return False

    to_do_copy = None

    for item in to_dos_list:
        if item["id"] == to_do_id:
            to_do_copy = item
            break
        continue

    if not to_do_copy:
        print("Invalid Id")
        return False

    to_dos_list.remove(to_do_copy)

    to_dos_list.insert(new_place - 1, to_do_copy)

    try:
        with open(path_to_json, "w") as file:
            json.dump(json_data, file, indent=2)
            print("Success")
            return True
    except (FileNotFoundError, PermissionError, OSError, json.JSONDecodeError) as e:
        print(f"Error: {e}")
        return False
