# app/pages/01_Overview.py
import streamlit as st
import pandas as pd

from app.lib.kpis import (
    calc_velocity,
    calc_throughput,
    calc_carryover_rate,
    calc_cycle_time,
    calc_defect_ratio,
)
from app.lib.data_access import load_sprint_csv

st.set_page_config(page_title="Overview", layout="wide")
st.title("Overview")
st.caption("Using sample data in data/sample_sprint.csv")

@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

try:
    df = load_csv("data/sample_sprint.csv")
except FileNotFoundError:
    st.error("Missing file: data/sample_sprint.csv. Add it and refresh.")
    st.stop()

# Compute KPIs
vel = calc_velocity(df)
thr = calc_throughput(df)
car = calc_carryover_rate(df)
cyc = calc_cycle_time(df)
dr  = calc_defect_ratio(df)

# Layout
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

df = load_sprint_csv("data/sample_sprint.csv")
