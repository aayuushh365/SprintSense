from __future__ import annotations

import pathlib
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from app.lib.data_access import load_sprint_csv
from app.lib.schema import validate_and_normalize
from app.lib.forecast import velocity_history


SAMPLE_PATH = pathlib.Path("data") / "sample_sprint.csv"


def _get_validated_df() -> pd.DataFrame:
    """Retrieve validated dataframe from session_state or fall back to sample CSV."""
    if "validated_df" in st.session_state and st.session_state["validated_df"] is not None:
        return st.session_state["validated_df"]

    df_raw = load_sprint_csv(str(SAMPLE_PATH))
    df_valid = validate_and_normalize(df_raw, validate_rows=True)

    st.session_state["validated_df"] = df_valid
    st.session_state["data_source"] = f"Bundled sample CSV ({SAMPLE_PATH})"
    st.session_state["df_current"] = df_valid
    st.session_state["source_label"] = "Bundled sample CSV"

    return df_valid


def _get_velocity_history(df: pd.DataFrame, lookback_sprints: Optional[int]) -> pd.Series:
    """Return historical velocities for selected lookback window using velocity_history."""
    hist = velocity_history(df)
    if hist.empty:
        raise ValueError("No historical velocity data available.")

    if lookback_sprints is not None and lookback_sprints > 0:
        hist = hist.tail(lookback_sprints)

    return hist


def _simulate_completion_probability(
    hist: pd.Series,
    commitment_sp: float,
    draws: int,
    seed: Optional[int] = 42,
) -> dict:
    """Run a one step Monte Carlo simulation for velocity.

    Returns:
    - mean_velocity
    - p10, p50, p90
    - probability_meet_commitment (velocity >= commitment_sp)
    - samples (raw simulated velocities)
    """
    values = hist.values.astype(float)
    if values.size == 0:
        raise ValueError("Not enough historical data for simulation.")

    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=draws, replace=True)

    prob_meet = float((samples >= commitment_sp).mean()) if commitment_sp > 0 else 1.0

    return {
        "mean_velocity": float(samples.mean()),
        "p10": float(np.percentile(samples, 10)),
        "p50": float(np.percentile(samples, 50)),
        "p90": float(np.percentile(samples, 90)),
        "probability_meet_commitment": prob_meet,
        "samples": samples,
    }


def main() -> None:
    st.title("Predictive completion probability")

    df = _get_validated_df()
    source_label = st.session_state.get("source_label") or st.session_state.get("data_source")
    if source_label:
        st.caption(f"Data source: {source_label}")

    with st.expander("What this dashboard does", expanded=True):
        st.write(
            "This view estimates the probability that your team can meet the next sprint "
            "commitment using historical sprint velocities and Monte Carlo simulation."
        )

    base_hist = velocity_history(df)
    if base_hist.empty:
        st.error("No historical velocity data found. Check your dataset and KPIs.")
        return

    min_hist = float(base_hist.min())
    max_hist = float(base_hist.max())
    median_hist = float(base_hist.median())
    count_hist = int(base_hist.shape[0])

    with st.sidebar:
        st.header("Simulation settings")

        st.write(f"Historical sprints available: {count_hist}")

        lookback_default = min(6, count_hist)
        lookback_sprints = st.slider(
            "Use last N sprints for history",
            min_value=1,
            max_value=count_hist,
            value=lookback_default,
        )

        hist = _get_velocity_history(df, lookback_sprints)

        commitment_default = max(median_hist, min_hist)
        commitment_sp = st.number_input(
            "Planned commitment for next sprint (story points)",
            min_value=0.0,
            value=float(commitment_default),
            step=1.0,
        )

        draws = st.number_input(
            "Number of Monte Carlo simulations",
            min_value=500,
            max_value=20000,
            value=5000,
            step=500,
        )

        seed = st.number_input(
            "Random seed",
            min_value=0,
            max_value=9999,
            value=42,
            step=1,
        )

    st.subheader("Historical velocity snapshot")
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Sprints used", lookback_sprints)
    col_b.metric("Median velocity", f"{median_hist:.1f}")
    col_c.metric("Min velocity", f"{min_hist:.1f}")
    col_d.metric("Max velocity", f"{max_hist:.1f}")

    if commitment_sp <= 0:
        st.warning("Set a positive commitment value to run the simulation.")
        return

    try:
        result = _simulate_completion_probability(
            hist=hist,
            commitment_sp=commitment_sp,
            draws=int(draws),
            seed=int(seed),
        )
    except ValueError as exc:
        st.error(str(exc))
        return

    prob = result["probability_meet_commitment"]
    prob_pct = prob * 100.0

    if prob_pct >= 80:
        status_text = "High chance of completion"
        status_emoji = "✅"
    elif prob_pct >= 50:
        status_text = "Moderate chance of completion"
        status_emoji = "🟡"
    else:
        status_text = "Low chance of completion"
        status_emoji = "⚠️"

    st.subheader("Completion probability")
    col1, col2 = st.columns(2)
    col1.metric("Planned commitment (story points)", f"{commitment_sp:.1f}")
    col2.metric(
        "Probability of meeting commitment",
        f"{prob_pct:.1f}%",
        help="Estimated from Monte Carlo sampling of historical sprint velocities.",
    )

    st.write(f"{status_emoji} {status_text}")

    st.subheader("Velocity distribution vs commitment")

    samples = result["samples"]
    samples_df = pd.DataFrame({"sampled_velocity": samples})

    fig = px.histogram(
        samples_df,
        x="sampled_velocity",
        nbins=20,
        title="Simulated velocity distribution",
    )
    fig.add_vline(
        x=commitment_sp,
        line_dash="dash",
        annotation_text="Commitment",
        annotation_position="top right",
    )
    fig.update_layout(
        xaxis_title="Velocity (story points)",
        yaxis_title="Frequency",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Summary table")

    summary_rows = []
    for mult, label in [
        (0.8, "80% of commitment"),
        (1.0, "100% commitment"),
        (1.2, "120% of commitment"),
    ]:
        target = mult * commitment_sp
        prob_row = float((samples >= target).mean())
        summary_rows.append(
            {
                "target_label": label,
                "target_story_points": round(target, 1),
                "probability_meet_target": round(prob_row * 100.0, 1),
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(summary_df, use_container_width=True)

    st.download_button(
        label="Download simulation samples as CSV",
        data=samples_df.to_csv(index=False).encode("utf-8"),
        file_name="sprint_completion_simulation_samples.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
