import pandas as pd
from app.lib.schema import validate_and_normalize

def test_optional_nans_become_none():
    df = pd.DataFrame({
        "issue_id":["A-1"],
        "issue_type":["bug"],
        "status":["Done"],
        "story_points":[float("nan")],
        "assignee":[None],
        "reporter":[None],
        "created":[pd.Timestamp("2024-01-01", tz="UTC")],
        "updated":[pd.NaT],
        "resolved":[pd.Timestamp("2024-01-02", tz="UTC")],
        "sprint_id":["S1"],
        "sprint_name":[None],
        "sprint_start":[pd.Timestamp("2024-01-01", tz="UTC")],
        "sprint_end":[pd.Timestamp("2024-01-14", tz="UTC")],
        "parent_id":[pd.NA],
        "labels":[pd.NA],
        "priority":[pd.NA],
    })
    out = validate_and_normalize(df, validate_rows=True)
    rec = out.iloc[0].to_dict()
    assert rec["story_points"] is None
    assert rec["parent_id"] is None
