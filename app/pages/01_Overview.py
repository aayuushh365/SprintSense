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

st.set_page_config(page_title="Overview", layout="wide")
st.title("Overview")
st.caption("Upload a Jira-style CSV or use the bundled sample.")

# ---------- Session persistence ----------
SESSION_KEY = "validated_df"
SOURCE_KEY  = "data_source"
SHARED_DF_KEY  = "df_current"     # for other pages
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
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Use uploaded", type="primary", disabled=up is None):
            df_up = _validate_uploaded(up)
            st.session_state[SESSION_KEY] = df_up
            st.session_state[SOURCE_KEY]  = f"uploaded: {up.name}"
            st.session_state[SHARED_DF_KEY]  = df_up
            st.session_state[SHARED_SRC_KEY] = (
                f"Using {st.session_state[SOURCE_KEY]} · "
                f"{len(df_up)} rows · {df_up['sprint_id'].nunique()} sprint(s)"
            )
            st.toast("Loaded uploaded CSV.", icon="✅")
    with c2:
        if st.button("Use bundled sample"):
            df_sm = _read_and_validate("data/sample_sprint.csv")
            st.session_state[SESSION_KEY] = df_sm
            st.session_state[SOURCE_KEY]  = "sample: data/sample_sprint.csv"
            st.session_state[SHARED_DF_KEY]  = df_sm
            st.session_state[SHARED_SRC_KEY] = (
                f"Using {st.session_state[SOURCE_KEY]} · "
                f"{len(df_sm)} rows · {df_sm['sprint_id'].nunique()} sprint(s)"
            )
            st.toast("Loaded sample CSV.", icon="📦")

# Fallback on first load
if SESSION_KEY not in st.session_state:
    df0 = _read_and_validate("data/sample_sprint.csv")
    st.session_state[SESSION_KEY] = df0
    st.session_state[SOURCE_KEY]  = "sample: data/sample_sprint.csv"
    st.session_state[SHARED_DF_KEY]  = df0
    st.session_state[SHARED_SRC_KEY] = (
        f"Using {st.session_state[SOURCE_KEY]} · "
        f"{len(df0)} rows · {df0['sprint_id'].nunique()} sprint(s)"
    )

# Local handle + keep shared keys in sync
df_all = st.session_state[SESSION_KEY]
st.session_state[SHARED_DF_KEY]  = df_all
st.session_state[SHARED_SRC_KEY] = (
    f"Using {st.session_state[SOURCE_KEY]} · "
    f"{len(df_all)} rows · {df_all['sprint_id'].nunique()} sprint(s)"
)

st.info(st.session_state[SHARED_SRC_KEY])
st.caption(f"Data source: {st.session_state[SOURCE_KEY]}")

# =========================
# Week 2.7 — FILTERS
# =========================
st.sidebar.subheader("Filters")

def _opts(series: pd.Series):
    return sorted([x for x in series.dropna().astype(str).unique()])

all_sprints   = _opts(df_all["sprint_id"])
all_types     = _opts(df_all.get("issue_type", pd.Series(dtype=str)))
all_status    = _opts(df_all.get("status", pd.Series(dtype=str)))
all_assignees = _opts(df_all.get("assignee", pd.Series(dtype=str)))

sel_sprints   = st.sidebar.multiselect("Sprint", all_sprints, default=all_sprints)
sel_types     = st.sidebar.multiselect("Issue type", all_types, default=all_types)
sel_status    = st.sidebar.multiselect("Status", all_status, default=all_status)
sel_assignees = st.sidebar.multiselect("Assignee", all_assignees, default=all_assignees)

if st.sidebar.button("Reset filters"):
    sel_sprints, sel_types, sel_status, sel_assignees = all_sprints, all_types, all_status, all_assignees

# Apply filters
df = df_all.copy()
if sel_sprints:   df = df[df["sprint_id"].astype(str).isin(sel_sprints)]
if sel_types:     df = df[df["issue_type"].astype(str).isin(sel_types)]
if sel_status:    df = df[df["status"].astype(str).isin(sel_status)]
if sel_assignees: df = df[df["assignee"].astype(str).isin(sel_assignees)]

st.caption(f"Filtered: {len(df)} rows · {df['sprint_id'].nunique()} sprint(s)")

# ---------- KPI summary cards ----------
st.subheader("KPIs")
render_summary_cards(df)
st.markdown("---")

# ---------- Tables (on filtered df) ----------
vel = calc_velocity(df)
thr = calc_throughput(df)
car = calc_carryover_rate(df)
cyc = calc_cycle_time(df)
dr  = calc_defect_ratio(df)

c1, c2 = st.columns(2)
with c1:
    st.subheader("Velocity (story points) by sprint")
    st.dataframe(vel.round(2), use_container_width=True)
with c2:
    st.subheader("Throughput (issues) by sprint")
    st.dataframe(thr.round(2), use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    st.subheader("Carryover rate")
    st.dataframe(car.round(2), use_container_width=True)
with c4:
    st.subheader("Cycle time (median days)")
    st.dataframe(cyc.round(2), use_container_width=True)

st.subheader("Defect ratio")
st.dataframe(dr.round(2), use_container_width=True)
st.markdown("---")

# ---------- Charts (polished) ----------
st.subheader("Charts")
st.plotly_chart(tidy(px.bar(vel, x="sprint_id", y="velocity_sp"),
                     title="Velocity by sprint"), use_container_width=True)
st.plotly_chart(tidy(px.bar(thr, x="sprint_id", y="throughput_issues"),
                     title="Throughput by sprint"), use_container_width=True)
st.plotly_chart(tidy(px.line(car, x="sprint_id", y="carryover_rate", markers=True),
                     title="Carryover rate"), use_container_width=True)
st.plotly_chart(tidy(px.line(cyc, x="sprint_id", y="cycle_median_days", markers=True),
                     title="Cycle time (median days)"), use_container_width=True)
st.plotly_chart(tidy(px.line(dr, x="sprint_id", y="defect_ratio", markers=True),
                     title="Defect ratio"), use_container_width=True)

# ---------- Drill-down table + download ----------
st.subheader("Details")
cols = [
    "issue_id","issue_type","status","assignee","story_points",
    "created","resolved","sprint_id","sprint_name","priority","labels"
]
present = [c for c in cols if c in df.columns]
st.dataframe(df[present], use_container_width=True, hide_index=True)

st.download_button(
    "Download filtered issues (CSV)",
    data=df[present].to_csv(index=False).encode("utf-8"),
    file_name="filtered_issues.csv",
    mime="text/csv",
    use_container_width=True,
)
