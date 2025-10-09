from __future__ import annotations
import pandas as pd

REQUIRED_COLS = {
    "issue_id","issue_type","status","story_points",
    "created","resolved","sprint_id","sprint_start","sprint_end",
}

def load_sprint_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    # parse dates if present
    for c in ["created","updated","resolved","sprint_start","sprint_end","in_progress_start"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], utc=True, errors="coerce")

    # normalize types
    if "issue_type" in df.columns:
        df["issue_type"] = df["issue_type"].astype(str).str.strip().str.lower()
    if "status" in df.columns:
        df["status"] = df["status"].astype(str).str.strip().str.lower()
    return df
