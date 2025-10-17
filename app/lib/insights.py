from __future__ import annotations
import pandas as pd, numpy as np
from .kpis import calc_velocity

def _safe_num(s) -> pd.Series:
    """Convert a sequence to numeric Series and drop NaNs."""
    return pd.to_numeric(pd.Series(s), errors="coerce").dropna()

def velocity_insights(df: pd.DataFrame, fc: pd.DataFrame) -> list[tuple[str,str]]:
    """Derive short velocity commentary given history and forecast bands."""
    msgs: list[tuple[str,str]] = []
    vel = calc_velocity(df)
    hist = _safe_num(vel["velocity_sp"])
    if len(hist) < 3:
        msgs.append(("warning","Limited history. Add more sprints for a better forecast."))
        return msgs
    slope = hist.diff().dropna().mean()
    if abs(slope) < 0.2: msgs.append(("info","Velocity trend is flat/stable."))
    elif slope > 0:      msgs.append(("success","Velocity is trending upward."))
    else:                msgs.append(("warning","Velocity is trending downward."))
    mean, std = float(hist.mean()), float(hist.std(ddof=1))
    cv = (std/mean) if mean else np.inf
    if cv < 0.10: msgs.append(("success","Past velocity is very stable (low variability)."))
    elif cv < 0.25: msgs.append(("info","Past velocity variability is moderate."))
    else: msgs.append(("warning","Past velocity is volatile; expect wider forecast bands."))
    if {"p90","p10"}.issubset(fc.columns):
        band = _safe_num(fc["p90"]) - _safe_num(fc["p10"])
        if len(band) > 0:
            avg_spread = float(band.mean())
            if   avg_spread < 3: msgs.append(("success","Forecast uncertainty is low."))
            elif avg_spread < 6: msgs.append(("info","Forecast uncertainty is moderate."))
            else:                msgs.append(("warning","Forecast uncertainty is high."))
    return msgs
