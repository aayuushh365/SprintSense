import pandas as pd
import pytest
from app.lib.schema import validate_and_normalize

def _base():
    return pd.DataFrame({
        "issue_id":["A"],"issue_type":["story"],"status":["Done"],
        "story_points":[3],"created":["2025-07-01T00:00:00Z"],
        "sprint_id":["S1"],"sprint_start":["2025-07-01T00:00:00Z"],"sprint_end":["2025-07-15T00:00:00Z"],
    })

def test_ok():
    df = _base()
    out = validate_and_normalize(df)
    assert "sprint_id" in out.columns

def test_missing_cols():
    df = _base().drop(columns=["sprint_start"])
    with pytest.raises(ValueError):
        validate_and_normalize(df)

def test_row_validation_negative_points():
    df = _base()
    df.loc[0, "story_points"] = -1
    with pytest.raises(ValueError):
        validate_and_normalize(df)
