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
    d = df.copy()

    mask = (
        d["sprint_id"].notna()
        & d["sprint_start"].notna()
        & d["sprint_end"].notna()
        & d["resolved"].notna()
        & (d["resolved"] >= d["sprint_start"])
        & (d["resolved"] <= d["sprint_end"])
    )
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

def _committed_at_start(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=["sprint_id", "sprint_start"])
    d = _parse_dates(d, ["created", "sprint_start"])
    return d.loc[d["created"] <= d["sprint_start"]]

def _unfinished_at_end(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=["sprint_id", "sprint_end"])
    d = _parse_dates(d, ["resolved", "sprint_end"])
    return d.loc[d["resolved"].isna() | (d["resolved"] > d["sprint_end"])]

def calc_carryover_rate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Carryover = unfinished at sprint end ÷ total issues in the sprint.
    Matches tests that expect 1/4 for S1 and S2 in the sample data.
    -> [sprint_id, carryover_rate]
    """
    # denominator: all issues assigned to the sprint
    total = df.dropna(subset=["sprint_id"]).groupby("sprint_id")["issue_id"].count()

    # numerator: unfinished by sprint end
    unfinished = _unfinished_at_end(df).groupby("sprint_id")["issue_id"].count()

    out = pd.DataFrame({"sprint_id": sorted(set(df["sprint_id"].dropna()))})
    out["total"] = out["sprint_id"].map(total).fillna(0).astype(int)
    out["unfinished"] = out["sprint_id"].map(unfinished).fillna(0).astype(int)
    out["carryover_rate"] = out.apply(
        lambda r: (r["unfinished"] / r["total"]) if r["total"] else 0.0, axis=1
    )
    return out.sort_values("sprint_id", ignore_index=True)[["sprint_id", "carryover_rate"]]
def calc_cycle_time(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["resolved","sprint_start","sprint_end","in_progress_start","created"]
    d = _parse_dates(df, [c for c in cols if c in df.columns])
    d = _resolved_within_sprint(d).copy()
    base = "in_progress_start" if "in_progress_start" in d.columns else "created"
    d = d.dropna(subset=[base, "resolved"])
    d["cycle_days"] = (d["resolved"] - d[base]).dt.total_seconds() / 86400.0
    g = d.groupby("sprint_id")["cycle_days"]
    return g.median().reset_index(name="cycle_median_days").sort_values("sprint_id", ignore_index=True)

def calc_defect_ratio(df: pd.DataFrame) -> pd.DataFrame:
    d = _resolved_within_sprint(df)
    total = d.groupby("sprint_id")["issue_id"].count()
    bugs = d.loc[d["issue_type"].str.lower() == "bug"].groupby("sprint_id")["issue_id"].count()
    out = pd.DataFrame({"sprint_id": sorted(set(d["sprint_id"]))})
    out["total"] = out["sprint_id"].map(total).fillna(0).astype(int)
    out["bugs"]  = out["sprint_id"].map(bugs).fillna(0).astype(int)
    out["defect_ratio"] = out.apply(lambda r: (r["bugs"]/r["total"]) if r["total"] else 0.0, axis=1)
    return out.sort_values("sprint_id", ignore_index=True)[["sprint_id","defect_ratio"]]
