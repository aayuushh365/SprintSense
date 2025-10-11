# app/lib/ui_kpis.py
from __future__ import annotations

import pandas as pd
import streamlit as st

from .kpis import (
    calc_velocity, calc_throughput, calc_carryover_rate,
    calc_cycle_time, calc_defect_ratio,
)

def _fmt(val, digits=2):
    """Pretty numeric formatting: 2dp, no trailing zeros."""
    if val is None:
        return "—"
    try:
        s = f"{float(val):.{digits}f}"
        # strip trailing zeros and dot
        s = s.rstrip("0").rstrip(".")
        return s
    except Exception:
        return str(val)

def render_summary_cards(df: pd.DataFrame) -> None:
    """
    Show KPI cards for the *latest* sprint, with deltas vs previous sprint.
    Numbers are nicely formatted to avoid long floats.
    """
    # Build per-sprint KPI table
    vel = calc_velocity(df)
    thr = calc_throughput(df)
    car = calc_carryover_rate(df)
    cyc = calc_cycle_time(df)
    dr  = calc_defect_ratio(df)

    kpi = (
        vel.merge(thr, on="sprint_id")
           .merge(car, on="sprint_id")
           .merge(cyc, on="sprint_id")
           .merge(dr,  on="sprint_id")
           .sort_values("sprint_id")
           .reset_index(drop=True)
    )

    if len(kpi) == 0:
        st.info("No KPI data to display.")
        return

    latest = kpi.iloc[-1]
    prev   = kpi.iloc[-2] if len(kpi) > 1 else None

    def pct_delta(cur, old):
        if old is None or old == 0 or pd.isna(old):
            return None
        try:
            return 100.0 * (cur - old) / abs(old)
        except Exception:
            return None

    # Prepare values + deltas
    vals = {
        "Velocity (SP)":        ("velocity_sp", 0),
        "Throughput (issues)":  ("throughput_issues", 0),
        "Carryover rate":       ("carryover_rate", 2),
        "Cycle time (days)":    ("cycle_median_days", 2),
        "Defect ratio":         ("defect_ratio", 2),
    }

    c1, c2, c3, c4, c5 = st.columns(5)
    cols = [c1, c2, c3, c4, c5]

    for (label, (col, digits)), container in zip(vals.items(), cols):
        cur = latest[col]
        old = prev[col] if prev is not None else None
        delta = pct_delta(cur, old)

        # Format value and delta
        value_str = _fmt(cur, digits)
        delta_str = None if delta is None else f"{_fmt(delta, 1)}%"

        with container:
            st.metric(label, value=value_str, delta=delta_str)
