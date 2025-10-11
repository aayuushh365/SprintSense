# app/pages/01_Overview.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import streamlit as st
import pandas as pd
import plotly.express as px

from app.lib.data_access import load_sprint_csv
from app.lib.schema import validate_and_normalize
from app.lib.kpis import (
    calc_velocity, calc_throughput, calc_carryover_rate,
    calc_cycle_time, calc_defect_ratio,
)
from app.lib.ui_kpis import render_summary_cards

st.set_page_config(page_title="Overview", layout="wide")
st.title("Overview")
st.caption("Upload a Jira-style CSV or use the bundled sample.")

# ---------- Session persistence ----------
SESSION_KEY = "validated_df"
SOURCE_KEY  = "data_source"

@st.cache_data(show_spinner=False)
def _read_and_validate(path: str) -> pd.DataFrame:
    return validate_and_normalize(load_sprint_csv(path))

@st.cache_data(show_spinner=False)
def _validate_uploaded(file: bytes) -> pd.DataFrame:
    df = pd.read_csv(file)
    return validate_and_normalize(df)

with st.expander("Upload sprint CSV", expanded=False):
    up = st.file_uploader("CSV", type=["csv"])
    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("Use uploaded", type="primary", disabled=up is None):
            st.session_state[SESSION_KEY] = _validate_uploaded(up)
            st.session_state[SOURCE_KEY] = f"uploaded: {up.name}"
            st.toast("Loaded uploaded CSV.", icon="✅")
    with c2:
        if st.button("Use bundled sample"):
            st.session_state[SESSION_KEY] = _read_and_validate("data/sample_sprint.csv")
            st.session_state[SOURCE_KEY] = "sample: data/sample_sprint.csv"
            st.toast("Loaded sample CSV.", icon="📦")

# Fallback on first load
if SESSION_KEY not in st.session_state:
    st.session_state[SESSION_KEY] = _read_and_validate("data/sample_sprint.csv")
    st.session_state[SOURCE_KEY] = "sample: data/sample_sprint.csv"

st.info(f"Using **{st.session_state[SOURCE_KEY]}** · "
        f"{len(st.session_state[SESSION_KEY])} rows · "
        f"{st.session_state[SESSION_KEY]['sprint_id'].nunique()} sprint(s)")

df = st.session_state[SESSION_KEY]

st.subheader("KPIs")
render_summary_cards(df)  # ⬅ summary cards

# ---------- Tables ----------
vel = calc_velocity(df)
thr = calc_throughput(df)
car = calc_carryover_rate(df)
cyc = calc_cycle_time(df)
dr  = calc_defect_ratio(df)

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

# ---------- Charts ----------
st.subheader("Charts")
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
