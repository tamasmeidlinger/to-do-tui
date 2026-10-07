from pathlib import Path

from app import start

if __name__ == "__main__":
    DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "to-do.json"
    start(DATA_PATH)
