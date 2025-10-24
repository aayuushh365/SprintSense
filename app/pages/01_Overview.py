import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import streamlit as st
import pandas as pd
import plotly.express as px

from app.lib.plot_helpers import tidy
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

# -----------------------------------------------------------------------------
# Page setup
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Overview", layout="wide")
st.title("Overview")
st.caption("Upload a Jira-style CSV or use the bundled sample.")

# -----------------------------------------------------------------------------
# Session keys (shared across pages)
# -----------------------------------------------------------------------------
SESSION_KEY      = "validated_df"        # canonical sprint dataframe currently in use
SOURCE_KEY       = "data_source"         # human string like 'uploaded: foo.csv'
SHARED_DF_KEY    = "df_current"          # same df for other pages
SHARED_SRC_KEY   = "source_label"        # "Using X · N rows · M sprint(s)"
LAST_MAPPING_KEY = "_last_mapping"       # remember column mapping choices within session
LAST_PREVIEW_KEY = "_last_preview"       # preview of last loaded df head()

# -----------------------------------------------------------------------------
# Cached helpers
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _read_and_validate(path: str) -> pd.DataFrame:
    """Load known-good CSV from disk and fully validate."""
    return validate_and_normalize(load_sprint_csv(path))

@st.cache_data(show_spinner=False)
def _load_csv_bytes(file) -> pd.DataFrame:
    """Read raw uploaded CSV bytes into a DataFrame. No validation here."""
    return pd.read_csv(file)

# -----------------------------------------------------------------------------
# Mapping UI for arbitrary uploads
# -----------------------------------------------------------------------------
def _mapping_ui(df_raw: pd.DataFrame) -> pd.DataFrame | None:
    """
    Show column mapping screen.
    - Suggest mappings from infer_mapping()
    - Reuse LAST_MAPPING_KEY if possible
    - Live preview of adapted/validated data
    - Returns validated df if user clicks Confirm mapping
    """
    st.markdown("#### Map columns")
    st.caption(
        "Map your CSV headers to SprintSense fields. "
        "We’ll try to guess. You can adjust. "
        "Your choices are remembered for this session."
    )

    # 1. auto-detect candidate mapping from column names
    detected = infer_mapping(df_raw)  # {canonical_field -> candidate_col}

    # 2. if we have a remembered mapping from this session, prefer it
    remembered = st.session_state.get(LAST_MAPPING_KEY, {})
    if remembered:
        for logical_field, chosen_col in remembered.items():
            if chosen_col in df_raw.columns:
                detected[logical_field] = chosen_col

    # UI layout
    cols = st.columns(2)

    with cols[0]:
        st.subheader("Required")
        req_mapping = {}
        for logical_field in REQUIRED_CANONICAL:
            opts = ["<none>"] + list(df_raw.columns)
            default_val = detected.get(logical_field)
            default_idx = opts.index(default_val) if default_val in opts else 0

            req_mapping[logical_field] = st.selectbox(
                logical_field,
                options=opts,
                index=default_idx,
                key=f"map_req_{logical_field}",
            )

    with cols[1]:
        st.subheader("Optional")
        opt_mapping = {}
        for logical_field in OPTIONAL_CANONICAL:
            opts = ["<none>"] + list(df_raw.columns)
            default_val = detected.get(logical_field)
            default_idx = opts.index(default_val) if default_val in opts else 0

            opt_mapping[logical_field] = st.selectbox(
                logical_field,
                options=opts,
                index=default_idx,
                key=f"map_opt_{logical_field}",
            )

    # Merge everything into mapping {canonical_field -> original_column_or_None}
    mapping = {}
    for k, v in req_mapping.items():
        mapping[k] = None if v == "<none>" else v
    for k, v in opt_mapping.items():
        mapping[k] = None if v == "<none>" else v

    # Live preview of how data would look after mapping/normalization
    st.markdown("##### Preview")
    st.caption("This is what SprintSense will ingest after mapping and cleanup.")
    preview_df = None
    try:
        adapted_tmp = apply_mapping(df_raw, mapping)
        # validate rows = False so we can at least show shape/head even if some rows are still dirty
        preview_df = validate_and_normalize(adapted_tmp, validate_rows=False)
        st.dataframe(preview_df.head(10), use_container_width=True)
    except Exception as e:
        st.warning(f"Cannot preview yet: {e}")

    # Confirm / Cancel
    c1, c2 = st.columns([1, 1])
    with c1:
        proceed = st.button(
            "Confirm mapping",
            type="primary",
            use_container_width=True
        )
    with c2:
        cancel = st.button(
            "Cancel",
            type="secondary",
            use_container_width=True
        )

    if cancel:
        # bail out to the current dataset without mutating it
        st.stop()

    if proceed:
        try:
            adapted = apply_mapping(df_raw, mapping)
            df_clean = validate_and_normalize(adapted)

            # persist mapping + preview so next upload is easier
            st.session_state[LAST_MAPPING_KEY] = {
                k: v for k, v in mapping.items() if v is not None
            }
            st.session_state[LAST_PREVIEW_KEY] = df_clean.head(20)

            st.success("Upload mapped and validated.")
            return df_clean
        except Exception as e:
            st.error(f"Mapping/validation failed: {e}")
            return None

    return None

# -----------------------------------------------------------------------------
# Upload section (always visible at top)
# -----------------------------------------------------------------------------
with st.expander("Upload sprint CSV", expanded=False):
    up = st.file_uploader("CSV", type=["csv"])

    # "Use uploaded" -> try direct validate first. If validation fails,
    # we drop into manual mapping flow below.
    c1, c2 = st.columns([1, 1])
    with c1:
        clicked_use_uploaded = st.button(
            "Use uploaded",
            type="primary",
            disabled=(up is None),
        )
    with c2:
        clicked_use_sample = st.button(
            "Use bundled sample",
            type="secondary",
        )

    # Branch: bundled sample button
    if clicked_use_sample:
        df_sm = _read_and_validate("data/sample_sprint.csv")

        st.session_state[SESSION_KEY] = df_sm
        st.session_state[SOURCE_KEY]  = "sample: data/sample_sprint.csv"
        st.session_state[SHARED_DF_KEY]  = df_sm
        st.session_state[SHARED_SRC_KEY] = (
            f"Using {st.session_state[SOURCE_KEY]} · "
            f"{len(df_sm)} rows · {df_sm['sprint_id'].nunique()} sprint(s)"
        )
        st.session_state[LAST_PREVIEW_KEY] = df_sm.head(20)

        st.toast("Loaded sample CSV.", icon="📦")

    # Branch: user clicked "Use uploaded"
    if clicked_use_uploaded and up is not None:
        raw_df = _load_csv_bytes(up)
        try:
            # Try strict validation directly
            df_up = validate_and_normalize(raw_df)

            st.session_state[SESSION_KEY] = df_up
            st.session_state[SOURCE_KEY]  = f"uploaded: {up.name}"
            st.session_state[SHARED_DF_KEY]  = df_up
            st.session_state[SHARED_SRC_KEY] = (
                f"Using {st.session_state[SOURCE_KEY]} · "
                f"{len[df_up] if callable(getattr(df_up, '__len__', None)) else len(df_up)} rows · "
                f"{df_up['sprint_id'].nunique()} sprint(s)"
            )
            st.session_state[LAST_PREVIEW_KEY] = df_up.head(20)

            st.toast("Loaded uploaded CSV.", icon="✅")

        except Exception as e:
            # Direct validation failed, so show mapping UI inline.
            st.error(f"Validation failed: {e}")
            mapped_df = _mapping_ui(raw_df)

            if mapped_df is not None:
                st.session_state[SESSION_KEY] = mapped_df
                st.session_state[SOURCE_KEY]  = f"uploaded: {up.name}"
                st.session_state[SHARED_DF_KEY]  = mapped_df
                st.session_state[SHARED_SRC_KEY] = (
                    f"Using {st.session_state[SOURCE_KEY]} · "
                    f"{len(mapped_df)} rows · {mapped_df['sprint_id'].nunique()} sprint(s)"
                )
                st.session_state[LAST_PREVIEW_KEY] = mapped_df.head(20)

                st.toast("Loaded uploaded CSV (mapped).", icon="✅")

# -----------------------------------------------------------------------------
# If we still don't have a dataset in session (first page load), default to sample
# -----------------------------------------------------------------------------
if SESSION_KEY not in st.session_state:
    df0 = _read_and_validate("data/sample_sprint.csv")

    st.session_state[SESSION_KEY] = df0
    st.session_state[SOURCE_KEY]  = "sample: data/sample_sprint.csv"
    st.session_state[SHARED_DF_KEY]  = df0
    st.session_state[SHARED_SRC_KEY] = (
        f"Using {st.session_state[SOURCE_KEY]} · "
        f"{len(df0)} rows · {df0['sprint_id'].nunique()} sprint(s)"
    )
    st.session_state[LAST_PREVIEW_KEY] = df0.head(20)

# Always sync these aliases for other pages
df = st.session_state[SESSION_KEY]
st.session_state[SHARED_DF_KEY]  = df
st.session_state[SHARED_SRC_KEY] = (
    f"Using {st.session_state[SOURCE_KEY]} · "
    f"{len(df)} rows · {df['sprint_id'].nunique()} sprint(s)"
)

# -----------------------------------------------------------------------------
# Data source banner + preview
# -----------------------------------------------------------------------------
st.info(st.session_state[SHARED_SRC_KEY])
st.caption(f"Data source: {st.session_state[SOURCE_KEY]}")

if st.session_state.get(LAST_PREVIEW_KEY) is not None:
    with st.expander("Current data preview (first 20 rows)", expanded=False):
        st.dataframe(
            st.session_state[LAST_PREVIEW_KEY],
            use_container_width=True,
            height=300,
        )

# --- High-level summary row (Week 4.4) ---
st.markdown("### Summary")
col_a, col_b, col_c = st.columns(3)

# total issues in dataset
total_issues = len(df)

# avg cycle time in days (only for rows that have both created + resolved)
if {"created", "resolved"}.issubset(df.columns):
    created_dt = pd.to_datetime(df["created"], errors="coerce", utc=True)
    resolved_dt = pd.to_datetime(df["resolved"], errors="coerce", utc=True)
    valid_mask = created_dt.notna() & resolved_dt.notna()
    avg_cycle_days = (
        (resolved_dt[valid_mask] - created_dt[valid_mask])
        .dt.total_seconds()
        .div(86400.0)
        .mean()
    )
    if pd.isna(avg_cycle_days):
        avg_cycle_days_disp = "—"
    else:
        avg_cycle_days_disp = f"{avg_cycle_days:.1f} d"
else:
    avg_cycle_days_disp = "—"

# total story points delivered (sum of story_points where status looks Done/Closed and resolved in sprint window)
if "story_points" in df.columns:
    total_sp = pd.to_numeric(df["story_points"], errors="coerce").fillna(0).sum()
    total_sp_disp = f"{total_sp:.1f} SP"
else:
    total_sp_disp = "—"

with col_a:
    st.metric("Total issues", value=str(total_issues))
with col_b:
    st.metric("Avg cycle time", value=avg_cycle_days_disp)
with col_c:
    st.metric("Total story points", value=total_sp_disp)

st.markdown("---")

# KPI summary cards
st.subheader("KPIs")
render_summary_cards(df)
st.markdown("---")

# -----------------------------------------------------------------------------
# Per-sprint KPI tables
# -----------------------------------------------------------------------------
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

# Download cleaned CSV (what the app is actually using right now)
csv_bytes = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download cleaned CSV",
    data=csv_bytes,
    file_name="sprintsense_cleaned.csv",
    mime="text/csv",
    use_container_width=True,
)

st.markdown("---")

# -----------------------------------------------------------------------------
# Charts
# -----------------------------------------------------------------------------
st.subheader("Charts")


st.plotly_chart(
    tidy(
        px.bar(vel, x="sprint_id", y="velocity_sp"),
        title="Velocity by sprint",
        x_title="sprint_id",
        y_title="velocity_sp",
    ),
    use_container_width=True,
)

st.plotly_chart(
    tidy(
        px.bar(thr, x="sprint_id", y="throughput_issues"),
        title="Throughput by sprint",
        x_title="sprint_id",
        y_title="throughput_issues",
    ),
    use_container_width=True,
)

st.plotly_chart(
    tidy(
        px.line(car, x="sprint_id", y="carryover_rate", markers=True),
        title="Carryover rate",
        x_title="sprint_id",
        y_title="carryover_rate",
    ),
    use_container_width=True,
)

st.plotly_chart(
    tidy(
        px.line(cyc, x="sprint_id", y="cycle_median_days", markers=True),
        title="Cycle time (median days)",
        x_title="sprint_id",
        y_title="cycle_median_days",
    ),
    use_container_width=True,
)

st.plotly_chart(
    tidy(
        px.line(dr, x="sprint_id", y="defect_ratio", markers=True),
        title="Defect ratio",
        x_title="sprint_id",
        y_title="defect_ratio",
    ),
    use_container_width=True,
)
