# app/lib/ui_kpis.py
from __future__ import annotations
from typing import Dict, Tuple, List
import pandas as pd
import streamlit as st

from app.lib.kpis import (
    calc_velocity,
    calc_throughput,
    calc_carryover_rate,
    calc_cycle_time,
    calc_defect_ratio,
)

def _order_sprints(df: pd.DataFrame) -> List[str]:
    """Best-effort sprint ordering: prefer sprint_start; else alphanumeric."""
    if {"sprint_id", "sprint_start"}.issubset(df.columns) and df["sprint_start"].notna().any():
        tmp = df[["sprint_id", "sprint_start"]].drop_duplicates().sort_values("sprint_start")
    else:
        tmp = df[["sprint_id"]].drop_duplicates().sort_values("sprint_id", key=lambda s: s.astype(str))
    return tmp["sprint_id"].tolist()

def _last_two(series_by_sprint: pd.DataFrame, value_col: str) -> Tuple[float | None, float | None]:
    """Return (latest, previous) values given a 2-col frame [sprint_id, value_col]."""
    sids = series_by_sprint["sprint_id"].tolist()
    vals = series_by_sprint[value_col].tolist()
    if len(vals) == 0:
        return None, None
    if len(vals) == 1:
        return float(vals[-1]), None
    return float(vals[-1]), float(vals[-2])

def _delta_pct(curr: float | None, prev: float | None) -> float | None:
    if curr is None or prev in (None, 0):
        return None
    return round((curr - prev) / prev * 100.0, 1)

def compute_summary(df: pd.DataFrame) -> Dict[str, Dict[str, float | None]]:
    """Pure function (no Streamlit) → easy to test."""
    order = _order_sprints(df)

    vel = calc_velocity(df).set_index("sprint_id").loc[order].reset_index()
    thr = calc_throughput(df).set_index("sprint_id").loc[order].reset_index()
    car = calc_carryover_rate(df).set_index("sprint_id").loc[order].reset_index()
    cyc = calc_cycle_time(df).set_index("sprint_id").loc[order].reset_index()
    dr  = calc_defect_ratio(df).set_index("sprint_id").loc[order].reset_index()

    v_cur, v_prev = _last_two(vel, "velocity_sp")
    t_cur, t_prev = _last_two(thr, "throughput_issues")
    c_cur, c_prev = _last_two(car, "carryover_rate")
    y_cur, y_prev = _last_two(cyc, "cycle_median_days")
    d_cur, d_prev = _last_two(dr,  "defect_ratio")

    return {
        "Velocity (SP)":         {"value": v_cur, "delta_pct": _delta_pct(v_cur, v_prev)},
        "Throughput (issues)":   {"value": t_cur, "delta_pct": _delta_pct(t_cur, t_prev)},
        "Carryover rate":        {"value": c_cur, "delta_pct": _delta_pct(c_cur, c_prev)},
        "Cycle time (days)":     {"value": y_cur, "delta_pct": _delta_pct(y_cur, y_prev)},
        "Defect ratio":          {"value": d_cur, "delta_pct": _delta_pct(d_cur, d_prev)},
    }

def render_summary_cards(df: pd.DataFrame) -> None:
    """Top-of-page KPI cards with deltas."""
    metrics = compute_summary(df)

    cols = st.columns(len(metrics))
    for col, (label, m) in zip(cols, metrics.items()):
        val = "—" if m["value"] is None else m["value"]
        delta = None if m["delta_pct"] is None else (f"{m['delta_pct']}%")
        with col:
            st.metric(label, val, delta=delta)
