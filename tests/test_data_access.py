import pytest
from app.lib.data_access import load_sprint_csv

def test_load_sprint_csv_ok(tmp_path):
    p = tmp_path/"s.csv"
    p.write_text(
        "issue_id,issue_type,status,story_points,created,resolved,sprint_id,sprint_start,sprint_end\n"
        "X-1,story,Done,3,2025-01-01T00:00:00Z,2025-01-02T00:00:00Z,S1,2025-01-01T00:00:00Z,2025-01-14T00:00:00Z\n"
    )
    df = load_sprint_csv(str(p))
    assert set({"issue_id","issue_type","created"}) <= set(df.columns)

def test_load_sprint_csv_missing_cols(tmp_path):
    p = tmp_path/"bad.csv"
    p.write_text("issue_id\nX-1\n")
    with pytest.raises(ValueError):
        load_sprint_csv(str(p))
