import pandas as pd
from app.lib.ui_kpis import compute_summary

def _mini_df():
    return pd.DataFrame({
        "issue_id": ["A","B","C","D"],
        "issue_type": ["story","story","bug","story"],
        "status": ["Done","Done","Done","Done"],
        "story_points": [3,5,None,8],
        "created": ["2025-01-01","2025-01-02","2025-01-03","2025-01-16"],
        "resolved": ["2025-01-02","2025-01-03","2025-01-04","2025-01-20"],
        "sprint_id": ["S1","S1","S1","S2"],
        "sprint_start": ["2025-01-01","2025-01-01","2025-01-01","2025-01-15"],
        "sprint_end":   ["2025-01-14","2025-01-14","2025-01-14","2025-01-28"],
    })

def test_compute_summary_returns_all_keys():
    out = compute_summary(_mini_df())
    assert {"Velocity (SP)","Throughput (issues)","Carryover rate","Cycle time (days)","Defect ratio"} <= set(out.keys())
