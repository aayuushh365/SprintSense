from __future__ import annotations
import numpy as np
import pandas as pd

from .kpis import calc_velocity

def velocity_history(df: pd.DataFrame) -> pd.Series:
    """Return historical sprint velocity as a Series (one value per sprint)."""
    v = calc_velocity(df).rename(columns={"velocity_sp": "velocity_sp"})
    # return just the velocity series, ordered by sprint_id already in calc_velocity
    return v["velocity_sp"]

def mc_velocity_forecast(df_or_series: pd.DataFrame | pd.Series, *, horizon: int, draws: int = 8000) -> pd.DataFrame:
    """
    Monte-Carlo forecast on sprint velocity.
    Accepts either a full DataFrame (we'll compute history) or a precomputed Series of velocity.
    Returns a DataFrame with columns: step, mean, p10, p50, p90
    """
    # Accept either DataFrame (compute history) or Series (use directly)
    if isinstance(df_or_series, pd.Series):
        hist = df_or_series.dropna().astype(float).to_numpy()
    else:
        hist = velocity_history(df_or_series).dropna().astype(float).to_numpy()

    if hist.size == 0:
        # empty history – return zeros to avoid crashes
        steps = np.arange(1, horizon + 1)
        return pd.DataFrame({"step": steps, "mean": 0.0, "p10": 0.0, "p50": 0.0, "p90": 0.0})

    rng = np.random.default_rng()
    draws_matrix = rng.choice(hist, size=(draws, horizon), replace=True)

    mean = draws_matrix.mean(axis=0)
    p10  = np.percentile(draws_matrix, 10, axis=0)
    p50  = np.percentile(draws_matrix, 50, axis=0)
    p90  = np.percentile(draws_matrix, 90, axis=0)

    out = pd.DataFrame({
        "step": np.arange(1, horizon + 1),
        "mean": mean,
        "p10":  p10,
        "p50":  p50,
        "p90":  p90,
    })
    return out
