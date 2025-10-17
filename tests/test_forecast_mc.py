import numpy as np
import pandas as pd
from app.lib.forecast import mc_velocity_forecast

def _df_with_velocity(vals):
    # Minimal DF that yields given velocities per sprint S1..Sn
    rows = []
    for i, v in enumerate(vals, start=1):
        rows.append({
            "issue_id": f"I-{i}",
            "issue_type": "story",
            "status": "Done",
            "story_points": v,
            "assignee": None, "reporter": None,
            "created": pd.Timestamp("2024-01-01", tz="UTC"),
            "updated": None,
            "resolved": pd.Timestamp(f"2024-01-{i:02d}", tz="UTC"),
            "sprint_id": f"S{i}", "sprint_name": None,
            "sprint_start": pd.Timestamp("2024-01-01", tz="UTC"),
            "sprint_end": pd.Timestamp("2024-12-31", tz="UTC"),
            "parent_id": None, "labels": None, "priority": None
        })
    return pd.DataFrame(rows)

def test_mc_velocity_forecast_deterministic(monkeypatch):
    # History [3, 5] → force sampler to always return [[3,5,3],[5,3,5],...]
    hist = np.array([3.0, 5.0])

    def fake_choice(a, size=None, replace=True):
        assert np.array_equal(a, hist)
        # shape (draws, horizon)
        draws, horizon = size
        pattern = np.tile(np.array([[3.0, 5.0, 3.0]], dtype=float), (draws, 1))
        return pattern[:, :horizon]

    monkeypatch.setattr(np.random, "choice", fake_choice)

    df = _df_with_velocity([3.0, 5.0])
    fc = mc_velocity_forecast(df, horizon=3, draws=1000)

    # With forced samples, mean=p50=pattern column values; p10=p90 same
    assert list(fc["step"]) == [1, 2, 3]
    assert np.allclose(fc["mean"].values, [3.0, 5.0, 3.0])
    assert np.allclose(fc["p50"].values,  [3.0, 5.0, 3.0])
    assert np.allclose(fc["p10"].values,  [3.0, 5.0, 3.0])
    assert np.allclose(fc["p90"].values,  [3.0, 5.0, 3.0])

def test_mc_velocity_forecast_empty_history():
    df = pd.DataFrame(columns=["sprint_id","story_points","status","resolved","sprint_start","sprint_end"])
    fc = mc_velocity_forecast(df, horizon=3, draws=1000)
    assert fc.empty
    assert list(fc.columns) == ["step","mean","p10","p50","p90"]
