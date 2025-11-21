import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.lib.data_access import load_sprint_csv
from app.lib.schema import validate_and_normalize
from app.lib.kpis import (
    calc_velocity,
    calc_throughput,
    calc_carryover_rate,
    calc_cycle_time,
    calc_defect_ratio,
)
from app.lib.forecast import mc_velocity_forecast
from app.lib.insights import velocity_insights
from app.lib.plot_helpers import tidy


def render_kpi_comparison(trends_df: pd.DataFrame, selected_kpis: list[str]) -> None:
    """Line chart comparing selected KPIs across sprints."""
    st.subheader("KPI comparison")

    if not selected_kpis:
        st.info("Select at least one KPI to compare.")
        return

    if trends_df.empty:
        st.warning("No data available for the selected sprint range.")
        return

    fig = go.Figure()

    for col in selected_kpis:
        if col not in trends_df.columns:
            continue

        fig.add_trace(
            go.Scatter(
                x=trends_df["sprint_id"],
                y=trends_df[col],
                mode="lines+markers",
                name=col.replace("_", " "),
            )
        )

    title_text = f"Selected KPI trends across {trends_df['sprint_id'].nunique()} sprint(s)"

    fig = tidy(
        fig,
        title=title_text,
        x_title="Sprint",
        y_title="Metric value",
    )

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        margin=dict(l=40, r=20, t=60, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)


st.set_page_config(page_title="Trends · SprintSense", layout="wide")
st.title("Trends")
st.caption(
    "Explore KPI trends, compare metrics, and run a Monte Carlo velocity forecast with what if scenarios."
)

# Load dataset from session, fallback to bundled sample
_df = st.session_state.get("validated_df", None)
if _df is None:
    _df = st.session_state.get("df_current", None)

source_label = st.session_state.get("data_source") or st.session_state.get("source_label")

if _df is None:
    _df = validate_and_normalize(load_sprint_csv("data/sample_sprint.csv"))
    sprints = _df["sprint_id"].nunique()
    rows = len(_df)
    source_label = f"Using sample: data/sample_sprint.csv · {rows} rows · {sprints} sprint(s)"

if source_label:
    st.info(source_label)

# Data quality hints
unique_sprints = _df["sprint_id"].nunique() if "sprint_id" in _df.columns else 0

required_cols = [
    "sprint_id",
    "story_points",
    "status",
    "resolved",
    "sprint_start",
    "sprint_end",
]

if set(required_cols).issubset(_df.columns):
    null_rate_velocity_inputs = (
        _df[required_cols]
        .isna()
        .mean(numeric_only=False)
        .sort_values(ascending=False)
    )
else:
    null_rate_velocity_inputs = None

if unique_sprints < 3:
    st.warning(
        f"Only {unique_sprints} sprint(s) detected. Trend lines and forecast will be noisy."
    )

if null_rate_velocity_inputs is not None and (null_rate_velocity_inputs > 0.2).any():
    st.warning(
        "Some key columns have a lot of missing data (>20 percent). "
        "Velocity and cycle time may be inaccurate."
    )

# KPI table
vel = calc_velocity(_df)
thr = calc_throughput(_df)
car = calc_carryover_rate(_df)
cyc = calc_cycle_time(_df)
dr = calc_defect_ratio(_df)

kpi = (
    vel.merge(thr, on="sprint_id")
    .merge(car, on="sprint_id")
    .merge(cyc, on="sprint_id")
    .merge(dr, on="sprint_id")
)

order = (
    _df.groupby("sprint_id")["sprint_start"]
    .min()
    .sort_values()
    .index
    .tolist()
)

kpi["sprint_id"] = pd.Categorical(kpi["sprint_id"], categories=order, ordered=True)
kpi = kpi.sort_values("sprint_id").reset_index(drop=True)

st.subheader("KPI trends (per sprint)")
st.dataframe(kpi, use_container_width=True)

# Filters for trends
st.sidebar.subheader("Filters")

all_sprints = list(kpi["sprint_id"].astype(str).unique())
sprint_range = st.sidebar.multiselect(
    "Select sprint(s)",
    all_sprints,
    default=all_sprints,
)

kpi_cols = [
    "velocity_sp",
    "throughput_issues",
    "carryover_rate",
    "cycle_median_days",
    "defect_ratio",
]

selected_kpis = st.sidebar.multiselect(
    "Select KPIs to compare",
    kpi_cols,
    default=["velocity_sp", "throughput_issues"],
)

kpi_filtered = kpi[kpi["sprint_id"].astype(str).isin(sprint_range)]

# KPI comparison chart
render_kpi_comparison(kpi_filtered, selected_kpis)

# Export KPI table
st.download_button(
    "Download KPI trends (CSV)",
    data=kpi.to_csv(index=False).encode("utf-8"),
    file_name="kpi_trends.csv",
    mime="text/csv",
    use_container_width=True,
)

# Individual KPI charts
st.subheader("Charts")

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(
        tidy(
            px.line(kpi, x="sprint_id", y="velocity_sp", markers=True),
            title="Velocity (SP)",
            x_title="Sprint",
            y_title="Story points (SP)",
        ),
        use_container_width=True,
    )
with c2:
    st.plotly_chart(
        tidy(
            px.line(kpi, x="sprint_id", y="throughput_issues", markers=True),
            title="Throughput (issues)",
            x_title="Sprint",
            y_title="Issues",
        ),
        use_container_width=True,
    )

c3, c4 = st.columns(2)
with c3:
    st.plotly_chart(
        tidy(
            px.line(kpi, x="sprint_id", y="carryover_rate", markers=True),
            title="Carryover rate",
            x_title="Sprint",
            y_title="Rate",
        ),
        use_container_width=True,
    )
with c4:
    st.plotly_chart(
        tidy(
            px.line(kpi, x="sprint_id", y="cycle_median_days", markers=True),
            title="Cycle time (median days)",
            x_title="Sprint",
            y_title="Days",
        ),
        use_container_width=True,
    )

st.plotly_chart(
    tidy(
        px.line(kpi, x="sprint_id", y="defect_ratio", markers=True),
        title="Defect ratio",
        x_title="Sprint",
        y_title="Share",
    ),
    use_container_width=True,
)

# Velocity forecast
st.header("Forecast (velocity)")

cA, cB = st.columns([1, 1])
with cA:
    horizon = st.number_input(
        "Horizon (sprints)",
        min_value=1,
        max_value=12,
        value=3,
        step=1,
    )
with cB:
    draws = st.number_input(
        "Monte Carlo draws",
        min_value=1000,
        max_value=100_000,
        value=8000,
        step=1000,
        format="%d",
    )

if kpi["sprint_id"].nunique() < 3:
    st.warning(
        "Forecast confidence is low (limited history). Add more sprints for better accuracy."
    )

# Use raw validated frame for forecast regardless of sidebar filters
df_raw = st.session_state.get("validated_df", None)
if df_raw is None:
    df_raw = st.session_state.get("df_current", None)
if df_raw is None:
    df_raw = validate_and_normalize(load_sprint_csv("data/sample_sprint.csv"))

fc_base = mc_velocity_forecast(
    df_raw,
    horizon=int(horizon),
    draws=int(draws),
)


def _infer_last_sprint_num(ids: pd.Series) -> int | None:
    for s in ids.astype(str)[::-1]:
        nums = "".join(ch if ch.isdigit() else " " for ch in s).split()
        if nums:
            try:
                return int(nums[-1])
            except ValueError:
                continue
    return None


last_num = _infer_last_sprint_num(kpi["sprint_id"])
if last_num is not None:
    fc_base["future_sprint"] = [f"S{last_num + i}" for i in fc_base["step"]]
else:
    fc_base["future_sprint"] = fc_base["step"].astype(str)

for level, msg in velocity_insights(df_raw, fc_base):
    fn = getattr(st, level, None)
    if callable(fn):
        fn(msg)
    else:
        st.write(msg)

st.dataframe(
    fc_base.rename(
        columns={
            "mean": "mean (SP)",
            "p10": "p10 (SP)",
            "p50": "p50 (SP)",
            "p90": "p90 (SP)",
        }
    ),
    use_container_width=True,
)

fig_fc = go.Figure()
fig_fc.add_trace(
    go.Scatter(
        x=fc_base["future_sprint"],
        y=fc_base["p90"],
        name="p90",
        line=dict(width=1.5),
    )
)
fig_fc.add_trace(
    go.Scatter(
        x=fc_base["future_sprint"],
        y=fc_base["p10"],
        name="p10",
        line=dict(width=1.5),
        fill="tonexty",
        fillcolor="rgba(0,123,255,0.15)",
    )
)
fig_fc.add_trace(
    go.Scatter(
        x=fc_base["future_sprint"],
        y=fc_base["p50"],
        name="p50 (median)",
        mode="lines+markers",
        line=dict(width=2),
    )
)
fig_fc = tidy(
    fig_fc,
    title="Velocity forecast",
    x_title="Future sprint",
    y_title="Story points (SP)",
)
fig_fc.update_layout(
    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.05)
)
st.plotly_chart(fig_fc, use_container_width=True)

st.caption(
    """How to read this forecast:
- p50 is the median. Half of future sprints land at or above this.
- p10 is the conservative case. Around 10 percent of sprints end lower than this.
- p90 is the optimistic case. Around 90 percent of sprints stay below this.
We build these bands by sampling historical velocity many times (Monte Carlo draws)."""
)

# What if scenarios
st.subheader("What if scenario")
if "scenarios" not in st.session_state:
    st.session_state["scenarios"] = {}
if "scenario_summaries" not in st.session_state:
    st.session_state["scenario_summaries"] = {}

with st.expander("Adjust assumptions", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        capacity_mult = st.slider(
            "Team capacity multiplier",
            0.5,
            1.5,
            1.00,
            0.05,
        )
    with c2:
        scope_growth = st.slider(
            "Scope growth per sprint (%)",
            0,
            30,
            0,
            1,
        )
    with c3:
        defect_uplift = st.slider(
            "Defect or bug rework uplift (%)",
            0,
            30,
            0,
            1,
        )

    eff_mult = capacity_mult / (1 + scope_growth / 100) / (1 + defect_uplift / 100)
    st.caption(f"Effective multiplier on velocity: **{eff_mult:.3f}**")

    fc_adj = fc_base.copy()
    for col in ["mean", "p10", "p50", "p90"]:
        fc_adj[col] = (fc_adj[col] * eff_mult).round(2)

    base_p50 = fc_base.loc[0, "p50"]
    adj_p50 = fc_adj.loc[0, "p50"]
    delta = adj_p50 - base_p50
    delta_pct = 0.0 if base_p50 == 0 else (delta / base_p50) * 100.0

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Next sprint p50 (base)", f"{base_p50:.1f} SP")
    with m2:
        st.metric("Next sprint p50 (what if)", f"{adj_p50:.1f} SP", f"{delta:+.1f} SP")
    with m3:
        st.metric("Change (%)", f"{delta_pct:+.1f}%")

    st.dataframe(
        fc_adj.rename(
            columns={
                "mean": "mean (SP)",
                "p10": "p10 (SP)",
                "p50": "p50 (SP)",
                "p90": "p90 (SP)",
            }
        ),
        use_container_width=True,
    )

    st.download_button(
        "Download adjusted forecast (CSV)",
        data=fc_adj.to_csv(index=False).encode("utf-8"),
        file_name="forecast_adjusted.csv",
        mime="text/csv",
        use_container_width=True,
    )

    s1, s2, s3 = st.columns([2, 2, 1])
    with s1:
        scen_name = st.text_input(
            "Scenario name",
            placeholder="e.g., plus 10 percent capacity, plus 5 percent scope",
        )
    with s2:
        if st.button(
            "Save scenario",
            use_container_width=True,
            disabled=(not scen_name.strip()),
        ):
            name = scen_name.strip()
            st.session_state["scenarios"][name] = {
                "capacity_mult": capacity_mult,
                "scope_growth": scope_growth,
                "defect_uplift": defect_uplift,
            }
            st.session_state["scenario_summaries"][name] = {
                "base_p50": float(base_p50),
                "what_if_p50": float(adj_p50),
                "delta_sp": float(delta),
                "delta_pct": float(delta_pct),
                "effective_multiplier": float(eff_mult),
            }
            st.success(f"Saved scenario: {name}")
    with s3:
        if st.button("Clear all", use_container_width=True, type="secondary"):
            st.session_state["scenarios"] = {}
            st.session_state["scenario_summaries"] = {}
            st.toast("Cleared scenarios.", icon="🧹")

    if st.session_state["scenarios"]:
        sc_load = st.selectbox(
            "Load existing scenario",
            options=["<select>"] + list(st.session_state["scenarios"].keys()),
            index=0,
        )
        if sc_load != "<select>":
            s = st.session_state["scenarios"][sc_load]
            st.info(
                f"Loaded **{sc_load}** → "
                f"capacity={s['capacity_mult']:.2f}, "
                f"scope={s['scope_growth']}%, "
                f"defects={s['defect_uplift']}%"
            )

    if st.session_state["scenario_summaries"]:
        st.markdown("**Saved scenarios overview**")
        scen_df = pd.DataFrame.from_dict(
            st.session_state["scenario_summaries"],
            orient="index",
        )
        scen_df.index.name = "scenario"
        scen_df = scen_df.reset_index()
        scen_df["delta_pct"] = scen_df["delta_pct"].round(1)
        scen_df["effective_multiplier"] = scen_df["effective_multiplier"].round(3)

        st.dataframe(
            scen_df.rename(
                columns={
                    "base_p50": "Base p50 (SP)",
                    "what_if_p50": "What if p50 (SP)",
                    "delta_sp": "Delta SP",
                    "delta_pct": "Delta %",
                    "effective_multiplier": "Effective velocity x",
                }
            ),
            use_container_width=True,
        )

# Overlay chart: base vs what if
st.subheader("Base vs what if (median)")
fig_overlay = go.Figure()
fig_overlay.add_trace(
    go.Scatter(
        x=fc_base["future_sprint"],
        y=fc_base["p50"],
        name="Base p50",
        mode="lines+markers",
    )
)
fig_overlay.add_trace(
    go.Scatter(
        x=fc_adj["future_sprint"],
        y=fc_adj["p50"],
        name="What if p50",
        mode="lines+markers",
    )
)
fig_overlay = tidy(
    fig_overlay,
    title="Median velocity: base vs what if",
    x_title="Future sprint",
    y_title="Story points (SP)",
)
fig_overlay.update_layout(
    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.05)
)
st.plotly_chart(fig_overlay, use_container_width=True)
