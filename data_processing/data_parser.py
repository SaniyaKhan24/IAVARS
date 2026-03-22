from typing import Iterable, List

import pandas as pd


REQUIRED_COLUMN = "Video Link"


def parse_video_links(df: pd.DataFrame) -> List[str]:
    """Extract cleaned, non-empty video links from a dataframe."""
    if REQUIRED_COLUMN not in df.columns:
        raise KeyError(f"Missing required column: {REQUIRED_COLUMN}")

    links: Iterable[str] = (
        str(value).strip()
        for value in df[REQUIRED_COLUMN].dropna().tolist()
    )
    return [link for link in links if link]
