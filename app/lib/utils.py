from __future__ import annotations
from typing import Iterable
import pandas as pd

def coerce_dates(df: pd.DataFrame, cols: Iterable[str]) -> None:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", utc=True)

def coerce_nums(df: pd.DataFrame, cols: Iterable[str]) -> None:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

def nan_to_none_for_optional(
    df: pd.DataFrame,
    optional_str_cols: Iterable[str],
    optional_num_cols: Iterable[str],
) -> None:
    for c in optional_str_cols:
        if c in df.columns:
            s = df[c].astype("object")
            df[c] = s.where(pd.notna(s), None)
    for c in optional_num_cols:
        if c in df.columns:
            s = df[c].astype("object")
            df[c] = s.where(pd.notna(s), None)
