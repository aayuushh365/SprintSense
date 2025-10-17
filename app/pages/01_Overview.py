import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from app.lib.plot_helpers import tidy

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

st.set_page_config(page_title="Overview · SprintSense", layout="wide")
st.title("Overview")
st.caption("Upload a Jira-style CSV or use the bundled sample. KPI cards show the latest sprint with % delta vs previous.")

SESSION_KEY = "validated_df"
SOURCE_KEY  = "data_source"
SHARED_DF_KEY  = "df_current"
SHARED_SRC_KEY = "source_label"

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
            df_up = _validate_uploaded(up)
            st.session_state[SESSION_KEY] = df_up
            st.session_state[SOURCE_KEY]  = f"uploaded: {up.name}"
            st.session_state[SHARED_DF_KEY]  = df_up
            st.session_state[SHARED_SRC_KEY] = f"Using {st.session_state[SOURCE_KEY]} · {len(df_up)} rows · {df_up['sprint_id'].nunique()} sprint(s)"
            st.toast("Loaded uploaded CSV.", icon="✅")
    with c2:
        if st.button("Use bundled sample"):
            df_sm = _read_and_validate("data/sample_sprint.csv")
            st.session_state[SESSION_KEY] = df_sm
            st.session_state[SOURCE_KEY]  = "sample: data/sample_sprint.csv"
            st.session_state[SHARED_DF_KEY]  = df_sm
            st.session_state[SHARED_SRC_KEY] = f"Using {st.session_state[SOURCE_KEY]} · {len(df_sm)} rows · {df_sm['sprint_id'].nunique()} sprint(s)"
            st.toast("Loaded sample CSV.", icon="📦")

if SESSION_KEY not in st.session_state:
    df0 = _read_and_validate("data/sample_sprint.csv")
    st.session_state[SESSION_KEY] = df0
    st.session_state[SOURCE_KEY]  = "sample: data/sample_sprint.csv"
    st.session_state[SHARED_DF_KEY]  = df0
    st.session_state[SHARED_SRC_KEY] = f"Using {st.session_state[SOURCE_KEY]} · {len(df0)} rows · {df0['sprint_id'].nunique()} sprint(s)"

df = st.session_state[SESSION_KEY]
st.session_state[SHARED_DF_KEY]  = df
st.session_state[SHARED_SRC_KEY] = f"Using {st.session_state[SOURCE_KEY]} · {len(df)} rows · {df['sprint_id'].nunique()} sprint(s)"

st.info(st.session_state[SHARED_SRC_KEY])

st.subheader("KPI summary")
render_summary_cards(df)
st.divider()

# KPI tables
vel = calc_velocity(df); thr = calc_throughput(df)
car = calc_carryover_rate(df); cyc = calc_cycle_time(df); dr = calc_defect_ratio(df)

c1, c2 = st.columns(2)
with c1:
    st.subheader("Velocity (SP) by sprint")
    st.dataframe(vel.round(2), use_container_width=True)
with c2:
    st.subheader("Throughput (issues) by sprint")
    st.dataframe(thr.round(2), use_container_width=True)
c3, c4 = st.columns(2)
with c3:
    st.subheader("Carryover rate")
    st.dataframe(car.round(3), use_container_width=True)
with c4:
    st.subheader("Cycle time (median days)")
    st.dataframe(cyc.round(2), use_container_width=True)
st.subheader("Defect ratio")
st.dataframe(dr.round(3), use_container_width=True)
st.divider()

# Charts (consistent titles, axes, hover)
st.subheader("Charts")
st.plotly_chart(
    tidy(px.bar(vel, x="sprint_id", y="velocity_sp"),
         title="Velocity by sprint", x_title="Sprint", y_title="Story points (SP)"),
    use_container_width=True
)
st.plotly_chart(
    tidy(px.bar(thr, x="sprint_id", y="throughput_issues"),
         title="Throughput by sprint", x_title="Sprint", y_title="Issues"),
    use_container_width=True
)
st.plotly_chart(
    tidy(px.line(car, x="sprint_id", y="carryover_rate", markers=True),
         title="Carryover rate", x_title="Sprint", y_title="Rate"),
    use_container_width=True
)
st.plotly_chart(
    tidy(px.line(cyc, x="sprint_id", y="cycle_median_days", markers=True),
         title="Cycle time", x_title="Sprint", y_title="Median days"),
    use_container_width=True
)
st.plotly_chart(
    tidy(px.line(dr, x="sprint_id", y="defect_ratio", markers=True),
         title="Defect ratio", x_title="Sprint", y_title="Share"),
    use_container_width=True
)
