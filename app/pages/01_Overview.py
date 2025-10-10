# app/pages/01_Overview.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import streamlit as st
import pandas as pd
import plotly.express as px

from app.lib.data_access import load_sprint_csv
from app.lib.schema import validate_and_normalize
from app.lib.kpis import (
    calc_velocity,
    calc_throughput,
    calc_carryover_rate,
    calc_cycle_time,
    calc_defect_ratio,
)

st.set_page_config(page_title="Overview", layout="wide")
st.title("Overview")
st.caption("Using sample data in data/sample_sprint.csv")
st.divider()
st.subheader("Charts")

@st.cache_data(show_spinner=False)
def load_and_validate(path: str) -> pd.DataFrame:
    df = load_sprint_csv(path)          # read CSV
    df = validate_and_normalize(df)     # enforce schema
    return df

try:
    df = load_and_validate("data/sample_sprint.csv")
except FileNotFoundError:
    st.warning("Add data/sample_sprint.csv to see KPIs.")
    st.stop()
except ValueError as e:
    st.error(f"Schema validation failed: {e}")
    st.stop()

# Compute KPIs
vel = calc_velocity(df)
thr = calc_throughput(df)
car = calc_carryover_rate(df)
cyc = calc_cycle_time(df)
dr  = calc_defect_ratio(df)

# Tables
c1, c2 = st.columns(2)
with c1:
    st.subheader("Velocity (story points) by sprint")
    st.dataframe(vel, use_container_width=True)
with c2:
    st.subheader("Throughput (issues) by sprint")
    st.dataframe(thr, use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    st.subheader("Carryover rate")
    st.dataframe(car, use_container_width=True)
with c4:
    st.subheader("Cycle time (median days)")
    st.dataframe(cyc, use_container_width=True)

st.subheader("Defect ratio")
st.dataframe(dr, use_container_width=True)

# Charts
st.plotly_chart(px.bar(vel, x="sprint_id", y="velocity_sp", title="Velocity by sprint"),
                use_container_width=True)
st.plotly_chart(px.bar(thr, x="sprint_id", y="throughput_issues", title="Throughput by sprint"),
                use_container_width=True)
st.plotly_chart(px.line(car, x="sprint_id", y="carryover_rate", markers=True, title="Carryover rate"),
                use_container_width=True)
st.plotly_chart(px.line(cyc, x="sprint_id", y="cycle_median_days", markers=True, title="Cycle time (median days)"),
                use_container_width=True)
st.plotly_chart(px.line(dr, x="sprint_id", y="defect_ratio", markers=True, title="Defect ratio"),
                use_container_width=True)
