from pathlib import Path

from utils.add_todo import add_todo
from utils.rearrange_todos import rearrange_todos
from utils.list_todos import list_todos
from utils.delete_todo import delete_todo
from utils.edit_todo import edit_todo


def main():
    PATH_TO_JSON = Path.cwd() / "data" / "to-do-test.json"

    list_todos("computer-systems", PATH_TO_JSON)

    delete_todo("computer-systems", PATH_TO_JSON, "e039966a")

    print("_______________")

    list_todos("computer-systems", PATH_TO_JSON)


if __name__ == "__main__":
    main()
