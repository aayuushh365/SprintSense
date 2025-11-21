import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

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
from app.lib.ui_kpis import render_summary_cards
from app.lib.adapt import (
    infer_mapping,
    apply_mapping,
    REQUIRED_CANONICAL,
    OPTIONAL_CANONICAL,
)
from app.lib.plot_helpers import tidy

TEMPLATE_COLUMNS = [
    "issue_id",
    "issue_type",
    "status",
    "story_points",
    "assignee",
    "reporter",
    "created",
    "updated",
    "resolved",
    "sprint_id",
    "sprint_name",
    "sprint_start",
    "sprint_end",
    "parent_id",  # optional
]


def make_template_df() -> pd.DataFrame:
    return pd.DataFrame(columns=TEMPLATE_COLUMNS)


SESSION_KEY = "validated_df"
SOURCE_KEY = "data_source"
SHARED_DF_KEY = "df_current"
SHARED_SRC_KEY = "source_label"
RAW_UPLOAD_KEY = "raw_upload_df"
MAPPING_KEY = "current_mapping"
ERROR_LOG_KEY = "upload_error_log"


st.set_page_config(page_title="Overview · SprintSense", layout="wide")
st.title("Overview")
st.caption("Upload a Jira style CSV or use the bundled sample.")


@st.cache_data(show_spinner=False)
def _read_and_validate(path: str) -> pd.DataFrame:
    df = load_sprint_csv(path)
    return validate_and_normalize(df)


@st.cache_data(show_spinner=False)
def _load_csv_bytes(file) -> pd.DataFrame:
    return pd.read_csv(file)


def _ensure_state_defaults() -> None:
    if SESSION_KEY not in st.session_state:
        df0 = _read_and_validate("data/sample_sprint.csv")
        st.session_state[SESSION_KEY] = df0
        st.session_state[SOURCE_KEY] = "sample: data/sample_sprint.csv"
        st.session_state[SHARED_DF_KEY] = df0
        st.session_state[SHARED_SRC_KEY] = (
            f"Using {st.session_state[SOURCE_KEY]} · {len(df0)} rows · "
            f"{df0['sprint_id'].nunique()} sprint(s)"
        )

    if RAW_UPLOAD_KEY not in st.session_state:
        st.session_state[RAW_UPLOAD_KEY] = None

    if MAPPING_KEY not in st.session_state:
        st.session_state[MAPPING_KEY] = None

    if ERROR_LOG_KEY not in st.session_state:
        st.session_state[ERROR_LOG_KEY] = None


def _data_dictionary() -> None:
    with st.expander("Data dictionary and KPI reference", expanded=False):
        st.markdown(
            """
            **Core columns**

            - `issue_id` unique ticket id like ABC 123
            - `issue_type` story, bug, task
            - `status` workflow status such as Done or In Progress
            - `story_points` numeric effort, can be blank
            - `created` when work started
            - `resolved` when work finished
            - `sprint_id` sprint label such as S12
            - `sprint_start` calendar start of sprint
            - `sprint_end` calendar end of sprint

            **Optional columns**

            - `assignee` who owned the work
            - `reporter` who raised the work
            - `sprint_name` friendly name such as Sprint 1 Jan 2024
            - `labels` and other text fields are carried through but not required

            **KPI definitions**

            - Velocity story points completed per sprint
            - Throughput count of issues completed per sprint
            - Carryover rate share of work that spills from one sprint into the next
            - Cycle time median days from created to resolved
            - Defect ratio share of bugs or defects against total issues
            """
        )


def _download_template_button_global() -> None:
    template_df = make_template_df()
    st.download_button(
        "Download CSV template",
        data=template_df.to_csv(index=False).encode("utf-8"),
        file_name="sprintsense_template.csv",
        mime="text/csv",
        use_container_width=True,
        key="download_template_global",
    )


def _render_health_check(df: pd.DataFrame) -> None:
    st.subheader("Health check")

    total_issues = len(df)
    n_sprints = df["sprint_id"].nunique() if "sprint_id" in df.columns else 0

    sp_per_sprint = None
    if "story_points" in df.columns and n_sprints > 0:
        sp_per_sprint = df.groupby("sprint_id")["story_points"].sum().mean()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Issues loaded", f"{total_issues}")
    with c2:
        st.metric("Sprints detected", f"{n_sprints}")
    with c3:
        if sp_per_sprint is not None:
            st.metric("Avg story points per sprint", f"{sp_per_sprint:.1f}")
        else:
            st.metric("Avg story points per sprint", "n/a")

    optional_missing = []
    for col in OPTIONAL_CANONICAL:
        if col not in df.columns or df[col].isna().all():
            optional_missing.append(col)

    notes = []
    if "resolved" in df.columns and df["resolved"].isna().all():
        notes.append("No resolved dates found. Cycle time may not be meaningful.")

    if "story_points" in df.columns and df["story_points"].fillna(0).sum() == 0:
        notes.append("Story points are all blank or zero. Velocity falls back to issue counts.")

    if optional_missing or notes:
        with st.expander("Data quality notes", expanded=False):
            if optional_missing:
                st.markdown(
                    "Missing optional fields: "
                    + ", ".join(sorted(optional_missing))
                )
            for n in notes:
                st.markdown(f"- {n}")


def _mapping_ui(df_raw: pd.DataFrame) -> None:
    st.markdown("#### Map columns")
    st.caption(
        "Map your CSV headers to SprintSense fields. Pre selections come from auto detection."
    )

    detected = infer_mapping(df_raw)
    stored = st.session_state.get(MAPPING_KEY) or {}

    cols_left, cols_right = st.columns(2)

    req_mapping: dict[str, str | None] = {}
    with cols_left:
        st.subheader("Required")
        for key in REQUIRED_CANONICAL:
            options = ["<none>"] + list(df_raw.columns)
            default = stored.get(key) or detected.get(key)

            if default in df_raw.columns:
                index = options.index(default)
            else:
                index = 0

            choice = st.selectbox(
                key,
                options=options,
                index=index,
                key=f"map_req_{key}",
            )
            req_mapping[key] = None if choice == "<none>" else choice

    opt_mapping: dict[str, str | None] = {}
    with cols_right:
        st.subheader("Optional")
        for key in OPTIONAL_CANONICAL:
            options = ["<none>"] + list(df_raw.columns)
            default = stored.get(key) or detected.get(key)

            if default in df_raw.columns:
                index = options.index(default)
            else:
                index = 0

            choice = st.selectbox(
                key,
                options=options,
                index=index,
                key=f"map_opt_{key}",
            )
            opt_mapping[key] = None if choice == "<none>" else choice

    mapping: dict[str, str | None] = {}
    mapping.update(req_mapping)
    mapping.update(opt_mapping)

    b1, b2, b3 = st.columns([1, 1, 1])
    with b1:
        confirm = st.button(
            "Confirm mapping",
            type="primary",
            use_container_width=True,
        )
    with b2:
        reset = st.button(
            "Reset mapping",
            type="secondary",
            use_container_width=True,
        )
    with b3:
        show_errors = st.button(
            "View last error report",
            use_container_width=True,
            disabled=st.session_state.get(ERROR_LOG_KEY) is None,
        )

    if reset:
        st.session_state[MAPPING_KEY] = None
        st.session_state[ERROR_LOG_KEY] = None
        st.toast("Mapping reset.", icon="🧹")

    if show_errors and st.session_state.get(ERROR_LOG_KEY):
        with st.expander("Upload error report", expanded=True):
            st.code(st.session_state[ERROR_LOG_KEY])
            st.download_button(
                "Download error log",
                data=str(st.session_state[ERROR_LOG_KEY]).encode("utf-8"),
                file_name="upload_error.log",
                mime="text/plain",
                use_container_width=True,
                key="download_error_log",
            )

    if confirm:
        try:
            adapted = apply_mapping(df_raw, mapping)
            df_clean = validate_and_normalize(adapted)

            st.session_state[SESSION_KEY] = df_clean
            st.session_state[SHARED_DF_KEY] = df_clean
            st.session_state[SHARED_SRC_KEY] = (
                f"Using mapped upload · {len(df_clean)} rows · "
                f"{df_clean['sprint_id'].nunique()} sprint(s)"
            )

            st.session_state[MAPPING_KEY] = mapping
            st.session_state[ERROR_LOG_KEY] = None

            st.success("Upload mapped and validated.")
        except Exception as exc:  # noqa: F841
            msg = str(exc)
            st.session_state[ERROR_LOG_KEY] = msg
            st.error(
                "Mapping or validation failed. Open the error report for details."
            )


_ensure_state_defaults()
_data_dictionary()

with st.expander("Upload sprint CSV", expanded=False):
    st.caption("Need a starting point for your data? Download the normalized CSV template.")

    tmpl_df = make_template_df()
    st.download_button(
        "Download CSV template",
        data=tmpl_df.to_csv(index=False).encode("utf-8"),
        file_name="sprintsense_template.csv",
        mime="text/csv",
        use_container_width=True,
        key="download_template_inside_upload",
    )

    st.divider()
    up = st.file_uploader("CSV", type=["csv"])

    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        use_uploaded = st.button(
            "Use uploaded",
            type="primary",
            use_container_width=True,
            disabled=up is None,
        )
    with c2:
        use_sample = st.button("Use bundled sample", use_container_width=True)
    with c3:
        _download_template_button_global()

    if use_uploaded and up is not None:
        try:
            df_raw = _load_csv_bytes(up)
            df_clean = validate_and_normalize(df_raw)

            st.session_state[SESSION_KEY] = df_clean
            st.session_state[SOURCE_KEY] = f"uploaded: {up.name}"
            st.session_state[SHARED_DF_KEY] = df_clean
            st.session_state[SHARED_SRC_KEY] = (
                f"Using {st.session_state[SOURCE_KEY]} · {len(df_clean)} rows · "
                f"{df_clean['sprint_id'].nunique()} sprint(s)"
            )

            st.session_state[RAW_UPLOAD_KEY] = df_raw
            st.session_state[ERROR_LOG_KEY] = None

            st.toast("Loaded uploaded CSV.", icon="✅")
        except Exception as exc:  # noqa: F841
            msg = str(exc)
            st.session_state[RAW_UPLOAD_KEY] = _load_csv_bytes(up)
            st.session_state[ERROR_LOG_KEY] = msg
            st.warning(
                "Validation failed. Scroll down to map columns and inspect the error report."
            )

    if use_sample:
        df_sm = _read_and_validate("data/sample_sprint.csv")

        st.session_state[SESSION_KEY] = df_sm
        st.session_state[SOURCE_KEY] = "sample: data/sample_sprint.csv"
        st.session_state[SHARED_DF_KEY] = df_sm
        st.session_state[SHARED_SRC_KEY] = (
            f"Using {st.session_state[SOURCE_KEY]} · {len(df_sm)} rows · "
            f"{df_sm['sprint_id'].nunique()} sprint(s)"
        )

        st.session_state[RAW_UPLOAD_KEY] = None
        st.session_state[ERROR_LOG_KEY] = None

        st.toast("Loaded sample CSV.", icon="📦")


if st.session_state.get(SHARED_SRC_KEY):
    st.info(st.session_state[SHARED_SRC_KEY])

df_current = st.session_state[SESSION_KEY]
st.session_state[SHARED_DF_KEY] = df_current

st.subheader("Upload health")
_render_health_check(df_current)

if st.session_state.get(RAW_UPLOAD_KEY) is not None:
    st.markdown("---")
    st.subheader("Column mapping")
    _mapping_ui(st.session_state[RAW_UPLOAD_KEY])

st.markdown("---")
st.subheader("Current data preview")

with st.expander("Current data preview (first 20 rows)", expanded=False):
    st.dataframe(df_current.head(20), use_container_width=True)

st.markdown("---")
st.subheader("Filters")

all_sprints = sorted(df_current["sprint_id"].astype(str).unique())

sidebar = st.sidebar
sidebar.subheader("Filters")

sel_sprints = sidebar.multiselect(
    "Select sprint(s)",
    all_sprints,
    default=all_sprints,
)

kpi_options = {
    "velocity_sp": "Velocity",
    "throughput_issues": "Throughput",
    "carryover_rate": "Carryover rate",
    "cycle_median_days": "Cycle time",
    "defect_ratio": "Defect ratio",
}

default_kpis = list(kpi_options.keys())

sel_kpis = sidebar.multiselect(
    "Select KPIs to show",
    default_kpis,
    default=default_kpis,
)

if sel_sprints:
    df_filtered = df_current[df_current["sprint_id"].astype(str).isin(sel_sprints)]
else:
    df_filtered = df_current.copy()

if df_filtered.empty:
    st.warning("No data for the selected sprint filters.")
    st.stop()

st.markdown("---")
st.subheader("Summary")

render_summary_cards(df_filtered)

vel = calc_velocity(df_filtered)
thr = calc_throughput(df_filtered)
car = calc_carryover_rate(df_filtered)
cyc = calc_cycle_time(df_filtered)
dr = calc_defect_ratio(df_filtered)

kpi = (
    vel.merge(thr, on="sprint_id")
    .merge(car, on="sprint_id")
    .merge(cyc, on="sprint_id")
    .merge(dr, on="sprint_id")
)

st.subheader("KPI table")
st.dataframe(kpi, use_container_width=True)

st.subheader("Charts")

c1, c2 = st.columns(2)

if "velocity_sp" in sel_kpis:
    with c1:
        st.plotly_chart(
            tidy(
                px.bar(
                    vel,
                    x="sprint_id",
                    y="velocity_sp",
                    title="Velocity by sprint",
                )
            ),
            use_container_width=True,
        )

if "throughput_issues" in sel_kpis:
    with c2:
        st.plotly_chart(
            tidy(
                px.bar(
                    thr,
                    x="sprint_id",
                    y="throughput_issues",
                    title="Throughput by sprint",
                )
            ),
            use_container_width=True,
        )

c3, c4 = st.columns(2)

if "carryover_rate" in sel_kpis:
    with c3:
        st.plotly_chart(
            tidy(
                px.line(
                    car,
                    x="sprint_id",
                    y="carryover_rate",
                    markers=True,
                    title="Carryover rate",
                )
            ),
            use_container_width=True,
        )

if "cycle_median_days" in sel_kpis:
    with c4:
        st.plotly_chart(
            tidy(
                px.line(
                    cyc,
                    x="sprint_id",
                    y="cycle_median_days",
                    markers=True,
                    title="Cycle time (median days)",
                )
            ),
            use_container_width=True,
        )

if "defect_ratio" in sel_kpis:
    st.plotly_chart(
        tidy(
            px.line(
                dr,
                x="sprint_id",
                y="defect_ratio",
                markers=True,
                title="Defect ratio",
            )
        ),
        use_container_width=True,
    )

st.markdown("---")
st.subheader("Download cleaned CSV")

st.download_button(
    "Download cleaned CSV",
    data=df_filtered.to_csv(index=False).encode("utf-8"),
    file_name="sprintsense_cleaned.csv",
    mime="text/csv",
    use_container_width=True,
    key="download_cleaned_csv",
)
