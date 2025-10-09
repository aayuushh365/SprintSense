import pandas as pd
from app.lib.kpis import calc_velocity, calc_throughput

def _sample_df():
    rows = [
        # sprint S1: two resolved with points 8 + 5, one bug (no points), one unfinished
        dict(issue_id="SS-1", issue_type="story", status="Done", story_points=8,  created="2025-07-01T09:00:00Z", resolved="2025-07-05T10:00:00Z",
             sprint_id="S1", sprint_start="2025-07-01T00:00:00Z", sprint_end="2025-07-14T23:59:59Z"),
        dict(issue_id="SS-2", issue_type="story", status="Done", story_points=5,  created="2025-07-02T11:00:00Z", resolved="2025-07-10T12:00:00Z",
             sprint_id="S1", sprint_start="2025-07-01T00:00:00Z", sprint_end="2025-07-14T23:59:59Z"),
        dict(issue_id="SS-3", issue_type="bug",   status="Done", story_points=None, created="2025-07-03T10:00:00Z", resolved="2025-07-12T15:00:00Z",
             sprint_id="S1", sprint_start="2025-07-01T00:00:00Z", sprint_end="2025-07-14T23:59:59Z"),
        dict(issue_id="SS-4", issue_type="story", status="In Progress", story_points=13, created="2025-07-04T09:00:00Z", resolved=None,
             sprint_id="S1", sprint_start="2025-07-01T00:00:00Z", sprint_end="2025-07-14T23:59:59Z"),
        # sprint S2: three resolved (8 + 5 + bug), one unfinished
        dict(issue_id="SS-5", issue_type="story", status="Done", story_points=8, created="2025-07-16T09:00:00Z", resolved="2025-07-20T10:00:00Z",
             sprint_id="S2", sprint_start="2025-07-15T00:00:00Z", sprint_end="2025-07-28T23:59:59Z"),
        dict(issue_id="SS-6", issue_type="bug",   status="Done", story_points=None, created="2025-07-18T08:00:00Z", resolved="2025-07-25T09:00:00Z",
             sprint_id="S2", sprint_start="2025-07-15T00:00:00Z", sprint_end="2025-07-28T23:59:59Z"),
        dict(issue_id="SS-7", issue_type="story", status="Done", story_points=5, created="2025-07-17T12:00:00Z", resolved="2025-07-27T14:00:00Z",
             sprint_id="S2", sprint_start="2025-07-15T00:00:00Z", sprint_end="2025-07-28T23:59:59Z"),
        dict(issue_id="SS-8", issue_type="story", status="To Do", story_points=3, created="2025-07-26T10:00:00Z", resolved=None,
             sprint_id="S2", sprint_start="2025-07-15T00:00:00Z", sprint_end="2025-07-28T23:59:59Z"),
    ]
    df = pd.DataFrame(rows)
    # align with schema column names expected in app
    df["assignee"] = None; df["reporter"] = None; df["updated"] = None
    df["sprint_name"] = None; df["parent_id"] = None; df["labels"] = None; df["priority"] = None
    return df

def test_calc_velocity_and_throughput():
    df = _sample_df()
    vel = calc_velocity(df)
    thr = calc_throughput(df)

    # velocity: S1 = 8+5=13, S2 = 8+5=13
    assert set(vel.columns) == {"sprint_id", "velocity_sp"}
    assert len(vel) == 2
    assert vel.loc[vel["sprint_id"] == "S1", "velocity_sp"].iloc[0] == 13
    assert vel.loc[vel["sprint_id"] == "S2", "velocity_sp"].iloc[0] == 13

    # throughput: S1 = 3 resolved, S2 = 3 resolved
    assert set(thr.columns) == {"sprint_id", "throughput_issues"}
    assert len(thr) == 2
    assert thr.loc[thr["sprint_id"] == "S1", "throughput_issues"].iloc[0] == 3
    assert thr.loc[thr["sprint_id"] == "S2", "throughput_issues"].iloc[0] == 3

from app.lib.kpis import calc_carryover_rate, calc_cycle_time, calc_defect_ratio

def test_more_kpis():
    df = _sample_df()
    car = calc_carryover_rate(df)
    cyc = calc_cycle_time(df)
    dr  = calc_defect_ratio(df)

    # carryover: S1 has SS-4 unfinished out of 4 committed -> 1/4 = 0.25; S2 has SS-8 unfinished out of 4 committed -> 1/4 = 0.25
    assert dict(zip(car.sprint_id, car.carryover_rate.round(2))) == {"S1": 0.25, "S2": 0.25}

    # cycle time medians should be positive numbers
    assert set(cyc.columns) == {"sprint_id","cycle_median_days"}
    assert (cyc.cycle_median_days > 0).all()

    # defect ratio: one bug resolved each sprint out of 3 resolved -> 1/3 ≈ 0.333
    vals = {k: round(v,3) for k,v in zip(dr.sprint_id, dr.defect_ratio)}
    assert vals == {"S1": 0.333, "S2": 0.333}
