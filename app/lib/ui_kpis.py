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
    order = _sprint_order(df)

    vel = calc_velocity(df)
    thr = calc_throughput(df)
    car = calc_carryover_rate(df)
    cyc = calc_cycle_time(df)
    dr  = calc_defect_ratio(df)

    # use human-readable keys to satisfy tests
    out = {
        "Velocity (SP)":        dict(zip(["value", "delta"], _latest_and_delta(vel, "velocity_sp", order))),
        "Throughput (issues)":  dict(zip(["value", "delta"], _latest_and_delta(thr, "throughput_issues", order))),
        "Carryover rate":       dict(zip(["value", "delta"], _latest_and_delta(car, "carryover_rate", order))),
        "Cycle time (days)":    dict(zip(["value", "delta"], _latest_and_delta(cyc, "cycle_median_days", order))),
        "Defect ratio":         dict(zip(["value", "delta"], _latest_and_delta(dr, "defect_ratio", order))),
    }
    return out



def _delta_badge(delta: float) -> str:
    arrow = "↑" if delta >= 0 else "↓"
    color = "green" if delta >= 0 else "red"
    return f":{color}[{arrow} {delta:.1f}%]"


def render_summary_cards(df: pd.DataFrame) -> None:
    """Small Streamlit cards row using compute_summary()."""
    data = compute_summary(df)  # keys like "Velocity (SP)", etc.
    cols = st.columns(5)

    labels = [
        "Velocity (SP)",
        "Throughput (issues)",
        "Carryover rate",
        "Cycle time (days)",
        "Defect ratio",
    ]

    for col, label in zip(cols, labels):
        with col:
            st.caption(label)
            st.markdown(f"## {data[label]['value']}")
            st.caption(_delta_badge(data[label]['delta']))