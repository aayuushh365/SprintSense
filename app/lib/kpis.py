# app/lib/kpis.py
import pandas as pd

# ---------- helpers ----------
def _parse_dates(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = pd.to_datetime(out[c], utc=True, errors="coerce")
    return out

def _resolved_within_sprint(df: pd.DataFrame) -> pd.DataFrame:
    """Rows whose resolved time falls within their sprint window."""
    d = df.dropna(subset=["sprint_id", "sprint_start", "sprint_end"])
    d = _parse_dates(d, ["resolved", "sprint_start", "sprint_end"])
    mask = d["resolved"].notna() & (d["resolved"] >= d["sprint_start"]) & (d["resolved"] <= d["sprint_end"])
    return d.loc[mask]

# ---------- KPIs to be imported by tests ----------
def calc_velocity(df: pd.DataFrame) -> pd.DataFrame:
    """Sum of story points resolved within each sprint. -> [sprint_id, velocity_sp]"""
    d = _resolved_within_sprint(df)
    d = d.dropna(subset=["story_points"])
    out = d.groupby("sprint_id")["story_points"].sum().reset_index(name="velocity_sp")
    return out.sort_values("sprint_id", ignore_index=True)

def calc_throughput(df: pd.DataFrame) -> pd.DataFrame:
    """Count of issues resolved within each sprint. -> [sprint_id, throughput_issues]"""
    d = _resolved_within_sprint(df)
    out = d.groupby("sprint_id")["issue_id"].count().reset_index(name="throughput_issues")
    return out.sort_values("sprint_id", ignore_index=True)
