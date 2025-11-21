from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from app.lib import kpis
from app.lib.data_access import load_sprint_csv
from app.lib.schema import validate_and_normalize


SAMPLE_PATH = "data/sample_sprint.csv"


def _get_validated_df() -> pd.DataFrame:
    if "validated_df" in st.session_state and st.session_state["validated_df"] is not None:
        return st.session_state["validated_df"]

    df_raw = load_sprint_csv(SAMPLE_PATH)
    df_valid = validate_and_normalize(df_raw, validate_rows=True)

    st.session_state["validated_df"] = df_valid
    st.session_state["data_source"] = f"Bundled sample CSV ({SAMPLE_PATH})"
    st.session_state["df_current"] = df_valid
    st.session_state["source_label"] = "Bundled sample CSV"

    return df_valid


def _build_kpi_table(df: pd.DataFrame) -> pd.DataFrame:
    vel = kpis.calc_velocity(df)
    thr = kpis.calc_throughput(df)
    cov = kpis.calc_carryover_rate(df)
    cyc = kpis.calc_cycle_time(df)
    dfx = kpis.calc_defect_ratio(df)

    kpi_df = vel.merge(thr, on="sprint_id", how="left")
    kpi_df = kpi_df.merge(cov, on="sprint_id", how="left")
    kpi_df = kpi_df.merge(cyc, on="sprint_id", how="left")
    kpi_df = kpi_df.merge(dfx, on="sprint_id", how="left")

    def _sprint_sort_key(x: str) -> int:
        if not isinstance(x, str):
            return 0
        digits = "".join(ch for ch in x if ch.isdigit())
        return int(digits) if digits else 0

    kpi_df = kpi_df.sort_values("sprint_id", key=lambda col: col.map(_sprint_sort_key))
    return kpi_df.reset_index(drop=True)


def _pick_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    cols_lower = {c.lower(): c for c in df.columns}
    for name in df.columns:
        lower = name.lower()
        for cand in candidates:
            if lower == cand or lower.replace(" ", "_") == cand:
                return name

    for cand in candidates:
        for lower, real in cols_lower.items():
            if cand in lower:
                return real

    return None


def _recent_slice(kpi_df: pd.DataFrame, last_n: int) -> pd.DataFrame:
    if last_n <= 0:
        return kpi_df
    if last_n >= len(kpi_df):
        return kpi_df
    return kpi_df.tail(last_n)


def _trend_percent(series: pd.Series) -> Optional[float]:
    series = series.dropna()
    if len(series) < 2:
        return None
    first = float(series.iloc[0])
    last = float(series.iloc[-1])
    if first == 0:
        return None
    return (last - first) / abs(first)


def _coefficient_of_variation(series: pd.Series) -> Optional[float]:
    series = series.dropna()
    if len(series) == 0:
        return None
    mean = float(series.mean())
    if mean == 0:
        return None
    std = float(series.std())
    return std / abs(mean)


def _build_insights(kpi_df: pd.DataFrame, last_n: int) -> Dict[str, Dict[str, str]]:
    recent = _recent_slice(kpi_df, last_n)

    vel_col = _pick_column(recent, ["velocity", "story_points_done", "points_done"])
    cov_col = _pick_column(recent, ["carryover_rate", "carryover"])
    def_col = _pick_column(recent, ["defect_ratio", "bug_ratio", "defects_ratio"])
    cyc_col = _pick_column(recent, ["cycle_time", "cycle_days"])

    insights: Dict[str, Dict[str, str]] = {}

    velocity_trend = _trend_percent(recent[vel_col]) if vel_col else None
    velocity_cv = _coefficient_of_variation(recent[vel_col]) if vel_col else None

    if velocity_trend is None or velocity_cv is None:
        insights["velocity"] = {
            "status": "neutral",
            "headline": "Velocity signal is unclear",
            "detail": "There is not enough clean data to analyse velocity trends for the selected window.",
        }
    else:
        trend_pct = round(velocity_trend * 100)
        if trend_pct > 5 and velocity_cv <= 0.3:
            insights["velocity"] = {
                "status": "positive",
                "headline": "Velocity is improving and stable",
                "detail": f"Over the last {last_n} sprints, average velocity increased about {trend_pct} percent with low variation. This supports more confident planning.",
            }
        elif trend_pct < -5:
            insights["velocity"] = {
                "status": "negative",
                "headline": "Velocity is trending down",
                "detail": f"Over the last {last_n} sprints, average velocity dropped about {abs(trend_pct)} percent. Investigate scope changes, blockers, or team capacity shifts.",
            }
        elif velocity_cv > 0.3:
            insights["velocity"] = {
                "status": "warning",
                "headline": "Velocity is unstable",
                "detail": f"Velocity fluctuates strongly across the last {last_n} sprints. High variation reduces predictability even if the average looks healthy.",
            }
        else:
            insights["velocity"] = {
                "status": "neutral",
                "headline": "Velocity is roughly stable",
                "detail": f"Velocity stayed within a moderate band over the last {last_n} sprints. No strong upward or downward trend.",
            }

    if cov_col and cov_col in recent:
        carry = recent[cov_col].dropna()
        avg_carry = float(carry.mean()) if not carry.empty else None
        carry_trend = _trend_percent(carry) if len(carry) >= 2 else None

        if avg_carry is None:
            insights["carryover"] = {
                "status": "neutral",
                "headline": "Carryover data is incomplete",
                "detail": "Carryover rate could not be calculated reliably for the selected window.",
            }
        else:
            avg_pct = int(round(avg_carry * 100))
            if avg_carry >= 0.4:
                if carry_trend and carry_trend > 0.05:
                    insights["carryover"] = {
                        "status": "negative",
                        "headline": "Carryover is high and rising",
                        "detail": f"On average, about {avg_pct} percent of work started in each sprint is not finished, and this share is increasing. This strongly impacts predictability.",
                    }
                else:
                    insights["carryover"] = {
                        "status": "warning",
                        "headline": "Carryover is consistently high",
                        "detail": f"On average, about {avg_pct} percent of work started per sprint is left unfinished. Consider tightening commitment or splitting large stories.",
                    }
            else:
                insights["carryover"] = {
                    "status": "positive",
                    "headline": "Carryover is under control",
                    "detail": f"Average carryover is about {avg_pct} percent across the last {last_n} sprints, which supports healthy predictability.",
                }
    else:
        insights["carryover"] = {
            "status": "neutral",
            "headline": "Carryover metric not available",
            "detail": "Carryover rate column was not found in the KPI table.",
        }

    if def_col and def_col in recent:
        defects = recent[def_col].dropna()
        avg_defect = float(defects.mean()) if not defects.empty else None
        def_trend = _trend_percent(defects) if len(defects) >= 2 else None

        if avg_defect is None:
            insights["defects"] = {
                "status": "neutral",
                "headline": "Defect signal is unclear",
                "detail": "Not enough data to analyse defect ratio trends.",
            }
        else:
            avg_pct = int(round(avg_defect * 100))
            if avg_defect >= 0.2 and def_trend and def_trend > 0.05:
                insights["defects"] = {
                    "status": "negative",
                    "headline": "Defect ratio is high and increasing",
                    "detail": f"On average, about {avg_pct} percent of completed work is defect type items, and this share is rising. This suggests growing quality problems.",
                }
            elif avg_defect >= 0.2:
                insights["defects"] = {
                    "status": "warning",
                    "headline": "Defect ratio is high",
                    "detail": f"Roughly {avg_pct} percent of completed work is defect items. Quality work is consuming a significant share of capacity.",
                }
            elif def_trend and def_trend < -0.05:
                insights["defects"] = {
                    "status": "positive",
                    "headline": "Defect ratio is improving",
                    "detail": f"Defect ratio is trending down over the last {last_n} sprints. Quality work is becoming a smaller share of throughput.",
                }
            else:
                insights["defects"] = {
                    "status": "neutral",
                    "headline": "Defect ratio is steady at a low level",
                    "detail": f"Defect ratio remains relatively low and stable across the last {last_n} sprints.",
                }
    else:
        insights["defects"] = {
            "status": "neutral",
            "headline": "Defect ratio not available",
            "detail": "Defect ratio column was not found in the KPI table.",
        }

    if cov_col and cov_col in recent:
        carry = recent[cov_col].dropna()
        if not carry.empty:
            avg_carry = float(carry.mean())
            predictability = max(0.0, min(1.0, 1.0 - avg_carry))
            if predictability >= 0.8:
                headline = "Predictability is strong"
                status = "positive"
            elif predictability >= 0.6:
                headline = "Predictability is moderate"
                status = "warning"
            else:
                headline = "Predictability is weak"
            insights["predictability"] = {
                "status": status,
                "headline": headline,
                "detail": f"Average predictability score over the last {last_n} sprints is about {round(predictability * 100)} percent based on 1 minus carryover rate.",
            }
        else:
            insights["predictability"] = {
                "status": "neutral",
                "headline": "Predictability score is unclear",
                "detail": "Carryover values were missing for the selected sprints.",
            }
    else:
        insights["predictability"] = {
            "status": "neutral",
            "headline": "Predictability metric not available",
            "detail": "Cannot compute predictability score without carryover data.",
        }

    if cyc_col and cyc_col in recent:
        cyc = recent[cyc_col].dropna()
        if cyc.empty:
            insights["cycle_time"] = {
                "status": "neutral",
                "headline": "Cycle time data is missing",
                "detail": "Cycle time values were not available for the selected sprints.",
            }
        else:
            median_cyc = float(cyc.median())
            cyc_trend = _trend_percent(cyc) if len(cyc) >= 2 else None
            if median_cyc > 6 and (not cyc_trend or cyc_trend >= 0):
                insights["cycle_time"] = {
                    "status": "warning",
                    "headline": "Cycle time is long",
                    "detail": f"Median cycle time is about {round(median_cyc, 1)} days across the last {last_n} sprints. Consider breaking down work or reducing WIP.",
                }
            elif cyc_trend and cyc_trend < -0.05:
                insights["cycle_time"] = {
                    "status": "positive",
                    "headline": "Cycle time is improving",
                    "detail": f"Cycle time is trending down over the last {last_n} sprints. Flow efficiency is improving.",
                }
            else:
                insights["cycle_time"] = {
                    "status": "neutral",
                    "headline": "Cycle time is stable",
                    "detail": f"Median cycle time is about {round(median_cyc, 1)} days with no strong trend up or down.",
                }
    else:
        insights["cycle_time"] = {
            "status": "neutral",
            "headline": "Cycle time not available",
            "detail": "Cycle time column was not found in the KPI table.",
        }

    return insights


def _overall_summary(insights: Dict[str, Dict[str, str]], last_n: int) -> str:
    predict = insights.get("predictability", {})
    vel = insights.get("velocity", {})
    carry = insights.get("carryover", {})
    defects = insights.get("defects", {})

    predict_headline = predict.get("headline", "Predictability signal is unclear")
    vel_headline = vel.get("headline", "Velocity signal is unclear")
    carry_headline = carry.get("headline", "Carryover signal is unclear")
    defects_headline = defects.get("headline", "Defect signal is unclear")

    return (
        f"Looking at the last {last_n} sprints, {predict_headline.lower()}. "
        f"{vel_headline} and {carry_headline.lower()}. "
        f"{defects_headline}"
    )


def _status_to_emoji(status: str) -> str:
    if status == "positive":
        return "✅"
    if status == "warning":
        return "🟡"
    if status == "negative":
        return "⚠️"
    return "ℹ️"


def _build_team_profile(
    df: pd.DataFrame,
    kpi_df: pd.DataFrame,
    insights: Dict[str, Dict[str, str]],
    last_n: int,
) -> Dict[str, str]:
    recent_kpi = _recent_slice(kpi_df, last_n)

    profile: Dict[str, str] = {}

    # Sprint cadence
    cadence_text = "Sprint cadence could not be inferred."
    if "sprint_start" in df.columns and "sprint_end" in df.columns:
        sprint_bounds = (
            df[["sprint_id", "sprint_start", "sprint_end"]]
            .dropna(subset=["sprint_id"])
            .drop_duplicates(subset=["sprint_id"])
        )
        sprint_bounds = sprint_bounds[
            sprint_bounds["sprint_id"].isin(recent_kpi["sprint_id"])
        ]
        if not sprint_bounds.empty:
            lengths = (sprint_bounds["sprint_end"] - sprint_bounds["sprint_start"]).dt.days
            if not lengths.empty:
                median_days = float(lengths.median())
                if 10 <= median_days <= 16:
                    cadence_text = "Team appears to work in a two week sprint cadence."
                elif 5 <= median_days <= 9:
                    cadence_text = "Team appears to work in a one week sprint cadence."
                elif 17 <= median_days <= 24:
                    cadence_text = "Team appears to work in a three week sprint cadence."
                else:
                    cadence_text = f"Team has an irregular sprint cadence of about {round(median_days)} days."
    profile["sprint_cadence"] = cadence_text

    # Team size
    team_size_text = "Team size could not be inferred."
    if "assignee" in df.columns:
        recent_ids = recent_kpi["sprint_id"].unique().tolist()
        recent_issues = df[df["sprint_id"].isin(recent_ids)]
        assignees = recent_issues["assignee"].dropna().unique().tolist()
        n = len(assignees)
        if n > 0:
            if n <= 4:
                team_size_text = f"Small team of about {n} active contributors."
            elif n <= 8:
                team_size_text = f"Medium sized team of about {n} active contributors."
            else:
                team_size_text = f"Larger team with roughly {n} active contributors."
    profile["team_size"] = team_size_text

    # Velocity summary
    vel_col = _pick_column(recent_kpi, ["velocity", "story_points_done", "points_done"])
    velocity_text = "Velocity summary is not available."
    if vel_col and vel_col in recent_kpi:
        vel_series = recent_kpi[vel_col].dropna()
        if not vel_series.empty:
            avg_vel = float(vel_series.mean())
            vel_cv = _coefficient_of_variation(vel_series)
            if vel_cv is not None:
                velocity_text = (
                    f"Average velocity is about {round(avg_vel, 1)} story points per sprint "
                    f"with a coefficient of variation around {round(vel_cv, 2)}."
                )
            else:
                velocity_text = f"Average velocity is about {round(avg_vel, 1)} story points per sprint."
    profile["velocity"] = velocity_text

    # Predictability summary from insights
    predict = insights.get("predictability", {})
    predict_headline = predict.get("headline", "Predictability signal is unclear.")
    predict_detail = predict.get("detail", "")
    profile["predictability"] = f"{predict_headline} {predict_detail}"

    return profile


def main() -> None:
    st.title("Team insights")

    df = _get_validated_df()
    source_label = st.session_state.get("source_label") or st.session_state.get("data_source")
    if source_label:
        st.caption(f"Data source: {source_label}")

    kpi_df = _build_kpi_table(df)
    total_sprints = len(kpi_df)

    with st.sidebar:
        st.header("Insight settings")
        st.write(f"Total sprints available: {total_sprints}")
        default_last_n = min(6, total_sprints) if total_sprints > 0 else 0
        last_n = st.slider(
            "Number of recent sprints to analyse",
            min_value=2,
            max_value=max(2, total_sprints),
            value=max(2, default_last_n),
        )

    if total_sprints < 2:
        st.error("Not enough sprint history to generate insights. At least 2 sprints are required.")
        return

    insights = _build_insights(kpi_df, last_n)
    summary_text = _overall_summary(insights, last_n)
    profile = _build_team_profile(df, kpi_df, insights, last_n)

    st.subheader("Summary")
    st.info(summary_text)

    st.subheader("Team profile")
    col_p1, col_p2 = st.columns(2)

    with col_p1:
        st.markdown("**Sprint cadence**")
        st.caption(profile["sprint_cadence"])
        st.markdown("**Velocity**")
        st.caption(profile["velocity"])

    with col_p2:
        st.markdown("**Team size**")
        st.caption(profile["team_size"])
        st.markdown("**Predictability**")
        st.caption(profile["predictability"])

    st.subheader("High level signals")
    col1, col2, col3 = st.columns(3)

    predict = insights.get("predictability", {})
    vel = insights.get("velocity", {})
    defects = insights.get("defects", {})

    with col1:
        st.markdown("**Predictability**")
        st.caption(predict.get("headline", "Not available"))

    with col2:
        st.markdown("**Velocity**")
        st.caption(vel.get("headline", "Not available"))

    with col3:
        st.markdown("**Quality**")
        st.caption(defects.get("headline", "Not available"))

    st.subheader("Detailed insights")

    for key, title in [
        ("velocity", "Velocity"),
        ("carryover", "Carryover"),
        ("predictability", "Predictability"),
        ("defects", "Defects and quality"),
        ("cycle_time", "Cycle time"),
    ]:
        info = insights.get(key)
        if not info:
            continue
        status = info.get("status", "neutral")
        emoji = _status_to_emoji(status)
        headline = info.get("headline", title)
        detail = info.get("detail", "")

        with st.expander(f"{emoji} {title}", expanded=False):
            st.write(headline)
            st.write(detail)


if __name__ == "__main__":
    main()
