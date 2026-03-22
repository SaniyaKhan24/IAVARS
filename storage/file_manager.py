import os


def create_folder(path: str) -> None:
    """Create a folder path if it does not exist."""
    os.makedirs(path, exist_ok=True)
