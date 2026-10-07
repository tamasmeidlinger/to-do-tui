"""Curses interface for the to-do app."""

from pathlib import Path

from .app import start

__all__ = ["start"]


def main() -> None:
    """Run the interface with the project's default data file."""
    start(Path.cwd() / "data" / "to-do-test.json")
