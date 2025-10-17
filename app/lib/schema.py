from __future__ import annotations
from typing import Optional, Iterable
from datetime import datetime
import pandas as pd
from pydantic import BaseModel, Field, ValidationError
from .utils import coerce_dates, coerce_nums, nan_to_none_for_optional

class Issue(BaseModel):
    """Typed schema for a single Jira-style issue row."""
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

CSV_HEADERS = [
    "issue_id","issue_type","status","story_points","assignee","reporter",
    "created","updated","resolved","sprint_id","sprint_name","sprint_start",
    "sprint_end","parent_id","labels","priority",
]

REQUIRED_COLS = {"issue_id","issue_type","status","story_points","created","sprint_id","sprint_start","sprint_end"}
DATE_COLS = {"created","updated","resolved","sprint_start","sprint_end"}
NUM_COLS  = {"story_points"}
OPTIONAL_STR_COLS = {"assignee","reporter","sprint_name","parent_id","labels","priority"}
OPTIONAL_NUM_COLS = {"story_points"}

def validate_and_normalize(df: pd.DataFrame, validate_rows: bool = True) -> pd.DataFrame:
    """Validate headers and rows, coerce dtypes, and return a clean DataFrame.

    Raises:
        ValueError: when required columns are missing or row validation fails.
    """
    problems = []
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        problems.append(f"Missing columns: {sorted(missing)}")
    out = df.copy()

    coerce_dates(out, DATE_COLS)
    coerce_nums(out, NUM_COLS)

    for c in ("issue_id","sprint_id","status"):
        if c in out.columns and out[c].isna().any():
            problems.append(f"Null values found in '{c}'")
    if problems:
        raise ValueError("; ".join(problems))

    if "sprint_id" in out.columns:
        out["sprint_id"] = out["sprint_id"].astype("string").astype(object)
    if "issue_type" in out.columns:
        out["issue_type"] = out["issue_type"].astype("string").str.strip().str.lower().astype(object)
    if "status" in out.columns:
        out["status"] = out["status"].astype("string").str.strip().str.title().astype(object)

    nan_to_none_for_optional(out, OPTIONAL_STR_COLS, OPTIONAL_NUM_COLS)

    if validate_rows:
        present = [c for c in CSV_HEADERS if c in out.columns]

        def _noneify_nan(rec: dict) -> dict:
            return {k: (None if pd.isna(v) else v) for k, v in rec.items()}

        errs = []
        for c in OPTIONAL_NUM_COLS:
            if c in out.columns:
                s = out[c].astype("object")
                out[c] = s.where(pd.notna(s), None)

        for c in OPTIONAL_STR_COLS:
            if c in out.columns:
                s = out[c].astype("object")
                out[c] = s.where(pd.notna(s), None)


        for idx, rec in enumerate(out[present].to_dict(orient="records")):
            try:
                Issue.model_validate(_noneify_nan(rec))
            except ValidationError as e:
                errs.append(f"row {idx}: {e.errors()}")
                if len(errs) >= 5:
                    errs.append("…more rows invalid")
                    break
        if errs:
            raise ValueError("Row validation failed: " + " | ".join(errs))
    return out

