import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import streamlit as st
import pandas as pd
import plotly.express as px

from app.lib.data_access import load_sprint_csv
from app.lib.schema import validate_and_normalize
from app.lib.kpis import (
    calc_velocity, calc_throughput, calc_carryover_rate,
    calc_cycle_time, calc_defect_ratio
)

st.set_page_config(page_title="Trends", layout="wide")
st.title("Trends")

# ---------- Load dataset (use session if present) ----------
df = st.session_state.get("df_current")
source_label = st.session_state.get("source_label")

if df is None:
    # Fallback to bundled sample
    df = validate_and_normalize(load_sprint_csv("data/sample_sprint.csv"))
    # helpful banner
    sprints = df["sprint_id"].nunique()
    rows = len(df)
    source_label = f"Using sample: data/sample_sprint.csv · {rows} rows · {sprints} sprint(s)"

st.info(source_label)

# ---------- Build per-sprint KPI table ----------
vel = calc_velocity(df)              # sprint_id, velocity_sp
thr = calc_throughput(df)            # sprint_id, throughput_issues
car = calc_carryover_rate(df)        # sprint_id, carryover_rate
cyc = calc_cycle_time(df)            # sprint_id, cycle_median_days
dr  = calc_defect_ratio(df)          # sprint_id, defect_ratio

kpi = (
    vel.merge(thr, on="sprint_id")
       .merge(car, on="sprint_id")
       .merge(cyc, on="sprint_id")
       .merge(dr,  on="sprint_id")
)

# Order sprints chronologically by their actual dates
order = (
    df.groupby("sprint_id")["sprint_start"].min()
      .sort_values()
      .index.tolist()
)
kpi["sprint_id"] = pd.Categorical(kpi["sprint_id"], categories=order, ordered=True)
kpi = kpi.sort_values("sprint_id").reset_index(drop=True)

st.subheader("KPI trends (per sprint)")
st.dataframe(kpi, use_container_width=True)

# ---------- Download export ----------
csv_bytes = kpi.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download KPI trends (CSV)",
    data=csv_bytes,
    file_name="kpi_trends.csv",
    mime="text/csv",
    use_container_width=True,
)

# ---------- Charts ----------
st.subheader("Charts")

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(px.line(kpi, x="sprint_id", y="velocity_sp",
                            markers=True, title="Velocity (SP)"),
                    use_container_width=True)
with c2:
    st.plotly_chart(px.line(kpi, x="sprint_id", y="throughput_issues",
                            markers=True, title="Throughput (issues)"),
                    use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    st.plotly_chart(px.line(kpi, x="sprint_id", y="carryover_rate",
                            markers=True, title="Carryover rate"),
                    use_container_width=True)
with c4:
    st.plotly_chart(px.line(kpi, x="sprint_id", y="cycle_median_days",
                            markers=True, title="Cycle time (median days)"),
                    use_container_width=True)

st.plotly_chart(px.line(kpi, x="sprint_id", y="defect_ratio",
                        markers=True, title="Defect ratio"),
                use_container_width=True)
