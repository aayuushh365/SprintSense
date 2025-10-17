from __future__ import annotations
from typing import Iterable
import pandas as pd

__all__ = ["coerce_dates", "coerce_nums", "nan_to_none_for_optional"]

def coerce_dates(df: pd.DataFrame, cols: Iterable[str]) -> None:
    """In-place: parse columns in `cols` to pandas datetime (UTC, NaT on errors)."""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", utc=True)

def coerce_nums(df: pd.DataFrame, cols: Iterable[str]) -> None:
    """In-place: parse columns in `cols` to numeric (NaN on errors)."""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

def nan_to_none_for_optional(df: pd.DataFrame, str_cols: Iterable[str], num_cols: Iterable[str]) -> None:
    """In-place: convert NaN to None for optional columns to satisfy Pydantic."""
    for c in str_cols:
        if c in df.columns:
            s = df[c]
            df[c] = s.where(pd.notna(s), None).astype("object")
    for c in num_cols:
        if c in df.columns:
            s = df[c]
            df[c] = s.where(pd.notna(s), None)
