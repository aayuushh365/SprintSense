import streamlit as st
import pandas as pd
from app.lib.kpis import calc_velocity, calc_throughput

st.title("Overview")

st.caption("Using sample data in data/sample_sprint.csv")
try:
    df = pd.read_csv("data/sample_sprint.csv")
    vel = calc_velocity(df)
    thr = calc_throughput(df)
    st.subheader("Velocity (story points) by sprint")
    st.dataframe(vel, use_container_width=True)
    st.subheader("Throughput (issues) by sprint")
    st.dataframe(thr, use_container_width=True)
except FileNotFoundError:
    st.warning("Add data/sample_sprint.csv to see KPIs.")
