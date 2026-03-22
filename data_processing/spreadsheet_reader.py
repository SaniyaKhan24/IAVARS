from pathlib import Path
from typing import Union

import pandas as pd


PathLike = Union[str, Path]


def read_spreadsheet(file_path: PathLike) -> pd.DataFrame:
    """Read an Excel or CSV spreadsheet into a DataFrame."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Spreadsheet not found: {path}")

    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix == ".csv":
        return pd.read_csv(path)

    raise ValueError(f"Unsupported file type: {suffix}")
