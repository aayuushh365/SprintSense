import pandas as pd

def velocity(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=["resolved","sprint_id","story_points"])
    return d.groupby("sprint_id")["story_points"].sum().reset_index(name="velocity_sp")

def throughput(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=["resolved","sprint_id"])
    return d.groupby("sprint_id")["issue_id"].count().reset_index(name="throughput_issues")