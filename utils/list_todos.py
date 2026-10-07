import json
from pathlib import Path


def list_todos(category_id: str, path_to_json: Path) -> bool | None:
    try:
        with open(path_to_json, "r") as file:
            json_data = json.load(file)
            for item in json_data:
                if item["id"] == category_id:
                    if len(item["toDos"]) == 0:
                        print(f"No items in {item['categoryName']}")
                    for index, todo in enumerate(item["toDos"], start=1):
                        print(f"{index}. - ID: {todo['id']} - {todo['title']}")
                    return True
                continue
            return False
    except (FileNotFoundError, PermissionError, OSError, json.JSONDecodeError) as e:
        print(e)
        return False
