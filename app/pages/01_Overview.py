# app/pages/01_Overview.py
import sys, os, io, hashlib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import streamlit as st
import pandas as pd
import plotly.express as px

from app.lib.schema import validate_and_normalize
from app.lib.data_access import load_sprint_csv
from app.lib.kpis import (
    calc_velocity,
    calc_throughput,
    calc_carryover_rate,
    calc_cycle_time,
    calc_defect_ratio,
)

st.set_page_config(page_title="Overview", layout="wide")
st.title("Overview")
st.caption("Upload a Jira-style CSV or use the bundled sample.")
st.divider()

# -------- caching helpers --------
@st.cache_data(show_spinner=False)
def _df_from_bytes(md5: str, raw: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(raw))
    return validate_and_normalize(df)

@st.cache_data(show_spinner=False)
def _df_from_sample(sample_path: str, mtime: float) -> pd.DataFrame:
    df = load_sprint_csv(sample_path)
    return validate_and_normalize(df)

def _hash_bytes(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()

# -------- file selection --------
csv_sample_path = "data/sample_sprint.csv"
uploaded = st.file_uploader("Upload sprint CSV", type=["csv"])

use_sample = False
df = None

try:
    if uploaded is not None:
        raw = uploaded.getvalue()
        md5 = _hash_bytes(raw)
        df = _df_from_bytes(md5, raw)
        st.success(f"Loaded `{uploaded.name}` · {len(df)} rows · "
                   f"{df['sprint_id'].nunique()} sprint(s)")
        st.caption(f"Cache key: {md5[:8]}")
    else:
        # fallback to sample
        mtime = os.path.getmtime(csv_sample_path)
        df = _df_from_sample(csv_sample_path, mtime)
        use_sample = True
        st.info(f"Using sample: `{csv_sample_path}` · {len(df)} rows · "
                f"{df['sprint_id'].nunique()} sprint(s)")
except FileNotFoundError:
    st.error("Missing `data/sample_sprint.csv`. Upload a CSV to proceed.")
    st.stop()
except ValueError as e:
    st.error(f"Schema validation failed: {e}")
    st.stop()

st.divider()
st.subheader("KPIs")

# -------- compute KPIs --------
vel = calc_velocity(df)
thr = calc_throughput(df)
car = calc_carryover_rate(df)
cyc = calc_cycle_time(df)
dr  = calc_defect_ratio(df)

# -------- tables --------
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

# -------- charts --------
st.divider()
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

# -------- cache controls --------
with st.expander("Cache"):
    if st.button("Clear cached data"):
        st.cache_data.clear()
        st.success("Cache cleared. Reload the page.")
