from __future__ import annotations
import pandas as pd

def _resolved_within_sprint(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    ok = (
        d["sprint_id"].notna()
        & d["sprint_start"].notna()
        & d["sprint_end"].notna()
        & d["resolved"].notna()
        & (d["resolved"] >= d["sprint_start"])
        & (d["resolved"] <= d["sprint_end"])
        & (d["status"].str.lower().str.contains("done") | d["status"].str.lower().str.contains("closed"))
    )
    return d[ok]

def calc_velocity(df: pd.DataFrame) -> pd.DataFrame:
    d = _resolved_within_sprint(df)
    out = d.groupby("sprint_id")["story_points"].sum(min_count=1).reset_index(name="velocity_sp").fillna(0.0)
    return out

def calc_throughput(df: pd.DataFrame) -> pd.DataFrame:
    d = _resolved_within_sprint(df)
    out = d.groupby("sprint_id")["issue_id"].count().reset_index(name="throughput_issues")
    return out

def calc_carryover_rate(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    in_sprint = d[d["sprint_id"].notna()]
    started = in_sprint.groupby("sprint_id")["issue_id"].count().reset_index(name="started")
    done = _resolved_within_sprint(df).groupby("sprint_id")["issue_id"].count().reset_index(name="done")
    merged = started.merge(done, on="sprint_id", how="left").fillna({"done": 0})
    merged["carryover_rate"] = ((merged["started"] - merged["done"]).clip(lower=0)) / merged["started"].replace({0: 1})
    return merged[["sprint_id","carryover_rate"]].round(3)

def calc_cycle_time(df: pd.DataFrame) -> pd.DataFrame:
    d = _resolved_within_sprint(df).copy()
    d["cycle_days"] = (d["resolved"] - d["created"]).dt.total_seconds() / 86400.0
    g = d.groupby("sprint_id")["cycle_days"]
    out = g.median().reset_index(name="cycle_median_days").round(2)
    return out

def calc_defect_ratio(df: pd.DataFrame) -> pd.DataFrame:
    d = _resolved_within_sprint(df).copy()
    d["is_defect"] = d["issue_type"].str.lower().str.contains("bug|defect")
    g = d.groupby("sprint_id")
    res = (g["is_defect"].sum() / g["issue_id"].count()).reset_index(name="defect_ratio").fillna(0.0).round(3)
    return res
