from __future__ import annotations
import numpy as np, pandas as pd
from .kpis import calc_velocity

def velocity_history(df: pd.DataFrame) -> pd.Series:
    """Return ordered historical velocity series as float."""
    v = calc_velocity(df)
    v = v.sort_values("sprint_id")["velocity_sp"].dropna().astype(float)
    return v

def mc_velocity_forecast(df: pd.DataFrame, horizon: int = 3, draws: int = 8000) -> pd.DataFrame:
    """Monte-Carlo forecast over historical velocity with bootstrap resampling.

    Returns columns: step, mean, p10, p50, p90
    """
    hist = velocity_history(df).values.astype(float)
    if hist.size == 0:
        return pd.DataFrame({"step": [], "mean": [], "p10": [], "p50": [], "p90": []})
    samples = np.random.choice(hist, size=(draws, horizon), replace=True)
    mean = samples.mean(axis=0)
    p10  = np.percentile(samples, 10, axis=0)
    p50  = np.percentile(samples, 50, axis=0)
    p90  = np.percentile(samples, 90, axis=0)
    return pd.DataFrame({"step": np.arange(1, horizon+1), "mean": mean, "p10": p10, "p50": p50, "p90": p90}).round(2)
