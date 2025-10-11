from __future__ import annotations

import pandas as pd
import streamlit as st

from .kpis import (
    calc_velocity,
    calc_throughput,
    calc_carryover_rate,
    calc_cycle_time,
    calc_defect_ratio,
)

__all__ = ["compute_summary", "render_summary_cards"]


def _sprint_order(df: pd.DataFrame) -> list[str]:
    """Chronological order of sprint ids based on sprint_start."""
    return (
        df.groupby("sprint_id")["sprint_start"]
        .min()
        .sort_values()
        .index.tolist()
    )


def _latest_and_delta(metric_df: pd.DataFrame, value_col: str, order: list[str]) -> tuple[float, float]:
    """Return (latest_value, pct_delta_vs_prev) for a per-sprint metric."""
    d = metric_df.copy()
    d["sprint_id"] = pd.Categorical(d["sprint_id"], categories=order, ordered=True)
    d = d.sort_values("sprint_id").reset_index(drop=True)
    vals = d[value_col].astype(float).tolist()

    if not vals:
        return 0.0, 0.0

    latest = float(vals[-1])
    prev = float(vals[-2]) if len(vals) > 1 else None

    if prev in (None, 0.0):
        delta = 0.0
    else:
        delta = (latest - prev) / prev * 100.0

    return round(latest, 2), round(delta, 1)


def compute_summary(df: pd.DataFrame) -> dict:
    """
    Compute headline KPIs and % deltas vs previous sprint.

    Returns a dict:
      {
        "velocity_sp": {"value": float, "delta": float},
        "throughput_issues": {...},
        "carryover_rate": {...},
        "cycle_median_days": {...},
        "defect_ratio": {...},
      }
    """
    order = _sprint_order(df)

    vel = calc_velocity(df)                 # sprint_id, velocity_sp
    thr = calc_throughput(df)               # sprint_id, throughput_issues
    car = calc_carryover_rate(df)           # sprint_id, carryover_rate
    cyc = calc_cycle_time(df)               # sprint_id, cycle_median_days
    dr  = calc_defect_ratio(df)             # sprint_id, defect_ratio

    out = {}
    out["velocity_sp"]        = dict(zip(["value", "delta"], _latest_and_delta(vel, "velocity_sp", order)))
    out["throughput_issues"]  = dict(zip(["value", "delta"], _latest_and_delta(thr, "throughput_issues", order)))
    out["carryover_rate"]     = dict(zip(["value", "delta"], _latest_and_delta(car, "carryover_rate", order)))
    out["cycle_median_days"]  = dict(zip(["value", "delta"], _latest_and_delta(cyc, "cycle_median_days", order)))
    out["defect_ratio"]       = dict(zip(["value", "delta"], _latest_and_delta(dr, "defect_ratio", order)))
    return out


def _delta_badge(delta: float) -> str:
    arrow = "↑" if delta >= 0 else "↓"
    color = "green" if delta >= 0 else "red"
    return f":{color}[{arrow} {delta:.1f}%]"


def render_summary_cards(df: pd.DataFrame) -> None:
    """Small Streamlit cards row using compute_summary()."""
    data = compute_summary(df)
    cols = st.columns(5)

    labels = [
        ("Velocity (SP)", "velocity_sp"),
        ("Throughput (issues)", "throughput_issues"),
        ("Carryover rate", "carryover_rate"),
        ("Cycle time (days)", "cycle_median_days"),
        ("Defect ratio", "defect_ratio"),
    ]

    for col, (label, key) in zip(cols, labels):
        with col:
            st.caption(label)
            st.markdown(f"## {data[key]['value']}")
            st.caption(_delta_badge(data[key]["delta"]))
