import pandas as pd
from app.lib.ui_kpis import compute_summary

def _mini_df():
    # Two sprints with resolved issues; second has higher velocity and throughput
    rows = [
        dict(issue_id="A1", issue_type="story", status="Done", story_points=3,
             assignee=None, reporter=None,
             created=pd.Timestamp("2024-01-01", tz="UTC"),
             updated=None, resolved=pd.Timestamp("2024-01-10", tz="UTC"),
             sprint_id="S1", sprint_name=None,
             sprint_start=pd.Timestamp("2024-01-01", tz="UTC"),
             sprint_end=pd.Timestamp("2024-01-15", tz="UTC"),
             parent_id=None, labels=None, priority=None),
        dict(issue_id="B1", issue_type="bug", status="Done", story_points=2,
             assignee=None, reporter=None,
             created=pd.Timestamp("2024-01-02", tz="UTC"),
             updated=None, resolved=pd.Timestamp("2024-01-12", tz="UTC"),
             sprint_id="S1", sprint_name=None,
             sprint_start=pd.Timestamp("2024-01-01", tz="UTC"),
             sprint_end=pd.Timestamp("2024-01-15", tz="UTC"),
             parent_id=None, labels=None, priority=None),
        dict(issue_id="C1", issue_type="story", status="Done", story_points=8,
             assignee=None, reporter=None,
             created=pd.Timestamp("2024-01-16", tz="UTC"),
             updated=None, resolved=pd.Timestamp("2024-01-20", tz="UTC"),
             sprint_id="S2", sprint_name=None,
             sprint_start=pd.Timestamp("2024-01-16", tz="UTC"),
             sprint_end=pd.Timestamp("2024-01-30", tz="UTC"),
             parent_id=None, labels=None, priority=None),
    ]
    return pd.DataFrame(rows)

def test_compute_summary_structure_and_types():
    df = _mini_df()
    summary = compute_summary(df)

    expected_keys = {
        "Velocity (SP)",
        "Throughput (issues)",
        "Carryover rate",
        "Cycle time (days)",
        "Defect ratio",
    }
    assert set(summary.keys()) == expected_keys

    # All metrics have value and delta numeric
    for v in summary.values():
        assert set(v.keys()) == {"value", "delta"}
        assert isinstance(v["value"], float) or isinstance(v["value"], int)
        assert isinstance(v["delta"], float) or isinstance(v["delta"], int)

def test_velocity_delta_sign():
    df = _mini_df()  # S1=5 SP, S2=8 SP → delta positive
    summary = compute_summary(df)
    assert summary["Velocity (SP)"]["value"] == 8.0
    assert summary["Velocity (SP)"]["delta"] > 0.0
