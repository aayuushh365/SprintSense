# app/lib/schema.py
from __future__ import annotations

from typing import Optional, Iterable
from datetime import datetime
import pandas as pd
from pydantic import BaseModel, Field, ValidationError

# ---------- Row schema ----------
class Issue(BaseModel):
    issue_id: str
    issue_type: str
    status: str
    story_points: Optional[float] = Field(default=None, ge=0)
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    created: datetime
    updated: Optional[datetime] = None
    resolved: Optional[datetime] = None
    sprint_id: str
    sprint_name: Optional[str] = None
    sprint_start: datetime
    sprint_end: datetime
    parent_id: Optional[str] = None
    labels: Optional[str] = None
    priority: Optional[str] = None

CSV_HEADERS: list[str] = [
    "issue_id","issue_type","status","story_points","assignee","reporter",
    "created","updated","resolved","sprint_id","sprint_name","sprint_start",
    "sprint_end","parent_id","labels","priority",
]

# ---------- DataFrame-level rules ----------
REQUIRED_COLS: set[str] = {
    "issue_id","issue_type","status",
    "story_points",           # column must exist (values may be None)
    "created","sprint_id","sprint_start","sprint_end",
}

DATE_COLS: set[str] = {"created","updated","resolved","sprint_start","sprint_end"}
NUM_COLS: set[str]  = {"story_points"}

# Columns that are optional *strings* in the schema
OPTIONAL_STR_COLS: set[str] = {"assignee","reporter","sprint_name","parent_id","labels","priority"}
# Columns that are optional *numbers*
OPTIONAL_NUM_COLS: set[str] = {"story_points"}

def _coerce_dates(df: pd.DataFrame, cols: Iterable[str]) -> None:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", utc=True)

def _coerce_nums(df: pd.DataFrame, cols: Iterable[str]) -> None:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

def _nan_to_none_for_optional(df: pd.DataFrame) -> None:
    """Replace NaN/NaT with None on optional columns so Pydantic accepts them."""
    for c in OPTIONAL_STR_COLS:
        if c in df.columns:
            s = df[c]
            # keep as Python objects; None for missing
            df[c] = s.where(pd.notna(s), None).astype("object")

    for c in OPTIONAL_NUM_COLS:
        if c in df.columns:
            s = df[c]
            # keep float/None (not NaN)
            df[c] = s.where(pd.notna(s), None)

def validate_and_normalize(df: pd.DataFrame, validate_rows: bool = True) -> pd.DataFrame:
    """
    Validate required columns, coerce types, convert NaN/NaT→None on optional
    fields, then (optionally) validate each row with Pydantic.
    """
    problems: list[str] = []

    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        problems.append(f"Missing columns: {sorted(missing)}")

    out = df.copy()

    # Type coercion first
    _coerce_dates(out, DATE_COLS)
    _coerce_nums(out, NUM_COLS)

    # Basic null checks on *identifiers* (must not be missing)
    for c in ("issue_id", "sprint_id", "status"):
        if c in out.columns and out[c].isna().any():
            problems.append(f"Null values found in '{c}'")

    if problems:
        raise ValueError("; ".join(problems))

    # Light normalization
    if "sprint_id" in out.columns:
        # leave as string-like; don't force "None"
        out["sprint_id"] = out["sprint_id"].astype("string").astype(object)
    if "issue_type" in out.columns:
        out["issue_type"] = out["issue_type"].astype("string").str.strip().str.lower().astype(object)
    if "status" in out.columns:
        out["status"] = out["status"].astype("string").str.strip().str.title().astype(object)

    # CRUCIAL: convert NaN/NaT → None for optional fields
    _nan_to_none_for_optional(out)


    if validate_rows:
        present = [c for c in CSV_HEADERS if c in out.columns]
        errs = []

        # Convert DF -> records AND ensure any NaN/NaT become proper None
        def _noneify(x):
            # pandas NA, numpy nan, NaT => None; leave other values as-is
            return None if (x is pd.NaT or (isinstance(x, float) and pd.isna(x)) or pd.isna(x)) else x

        records = out[present].to_dict(orient="records")
        # sanitize each record so Pydantic never sees NaN/NaT
        records = [{k: _noneify(v) for k, v in rec.items()} for rec in records]

        for idx, rec in enumerate(records):
            try:
                Issue.model_validate(rec)
            except ValidationError as e:
                errs.append(f"row {idx}: {e.errors()}")
                if len(errs) >= 5:
                    errs.append("…more rows invalid")
                    break
        if errs:
            raise ValueError("Row validation failed: " + " | ".join(errs))

    return out

