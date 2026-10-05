from __future__ import annotations

import pandas as pd
import streamlit as st

from data import google_sheet_url, load_schedule_from_csv, load_schedule_from_google_sheet
from gantt import create_gantt, create_high_level_gantt


st.set_page_config(
    page_title="Project Gantt Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2.5rem;
    }

    h1 {
        margin-bottom: 0.15rem;
    }

    [data-testid="stSidebar"] .stSelectbox {
        margin-bottom: 0.4rem;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.55rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=30)
def load_schedule():
    """Load the published Google Sheet, falling back to local sample data."""
    try:
        df = load_schedule_from_google_sheet()
        return df, "Live Google Sheet", None
    except Exception as exc:
        df = load_schedule_from_csv("sample_tasks.csv")
        return df, "Local fallback", str(exc)


def refresh_schedule() -> None:
    st.cache_data.clear()
    st.rerun()


def apply_filters(
    data: pd.DataFrame,
    section: str,
    status: str,
    member: str,
) -> pd.DataFrame:
    filtered = data.copy()

    if section != "All sections":
        filtered = filtered[filtered["Section"] == section].copy()

    if status != "All statuses":
        filtered = filtered[filtered["Status"] == status].copy()

    if member != "All team members":
        filtered = filtered[
            filtered["Owners"].apply(lambda owners: member in owners)
        ].copy()

    return filtered


df, data_source, data_error = load_schedule()

if df.empty:
    st.error("No project schedule data was found.")
    st.stop()

all_members = sorted({owner for owners in df["Owners"] for owner in owners})
all_sections = sorted(df["Section"].dropna().astype(str).unique().tolist())
all_statuses = sorted(
    df["Status"]
    .dropna()
    .astype(str)
    .loc[lambda s: s.str.strip() != ""]
    .unique()
    .tolist()
)

project_start = df["Start"].min()
project_finish = df["Finish"].max()
total_tasks = len(df)
completed_tasks = int((df["PercentComplete"] >= 100).sum())
average_completion = float(df["PercentComplete"].mean())

st.title("Project Gantt Dashboard")
st.caption("Interactive project schedule and team planning dashboard")

with st.sidebar:
    st.header("Schedule controls")
    st.caption(f"Data source: {data_source}")

    if data_source == "Local fallback" and data_error:
        with st.expander("Why is fallback data being used?"):
            st.code(data_error)

    refresh_col, sheet_col = st.columns(2)
    with refresh_col:
        if st.button("Refresh", use_container_width=True, type="primary"):
            refresh_schedule()
    with sheet_col:
        st.link_button("Sheet", google_sheet_url(), use_container_width=True)

    st.divider()
    st.subheader("Filters")

    # Compact dropdowns instead of Streamlit multiselect chips/bubbles.
    selected_section = st.selectbox(
        "Work section",
        options=["All sections"] + all_sections,
        index=0,
    )

    selected_status = st.selectbox(
        "Status",
        options=["All statuses"] + all_statuses,
        index=0,
    )

    selected_member = st.selectbox(
        "Team member",
        options=["All team members"] + all_members,
        index=0,
    )

    if st.button("Reset filters", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.divider()
    st.subheader("Project summary")
    st.metric("Tasks", total_tasks)
    st.metric("Completed", completed_tasks)
    st.metric("Average completion", f"{average_completion:.0f}%")

    if pd.notna(project_start):
        st.caption(f"Start: {project_start.strftime('%b %d, %Y')}")
    if pd.notna(project_finish):
        st.caption(f"Finish: {project_finish.strftime('%b %d, %Y')}")

filtered_df = apply_filters(
    df,
    selected_section,
    selected_status,
    selected_member,
)

overview_tab, detailed_tab, team_tab, table_tab = st.tabs(
    ["Overview", "Detailed Schedule", "Team View", "Task Table"]
)

with overview_tab:
    st.subheader("High-Level Project Schedule")
    st.caption("Major project phases rolled up from the detailed schedule.")

    if filtered_df.empty:
        st.info("No tasks match the current filters.")
    else:
        overview_fig = create_high_level_gantt(filtered_df)
        st.plotly_chart(
            overview_fig,
            use_container_width=True,
            config={
                "displaylogo": False,
                "responsive": True,
                "scrollZoom": False,
            },
        )

    c1, c2, c3, c4 = st.columns(4)
    visible_completed = int((filtered_df["PercentComplete"] >= 100).sum())
    visible_progress = (
        float(filtered_df["PercentComplete"].mean()) if not filtered_df.empty else 0.0
    )
    active_tasks = int(
        ((filtered_df["PercentComplete"] > 0) & (filtered_df["PercentComplete"] < 100)).sum()
    )

    c1.metric("Visible tasks", len(filtered_df))
    c2.metric("Completed tasks", visible_completed)
    c3.metric("Average progress", f"{visible_progress:.0f}%")
    c4.metric("In progress", active_tasks)

with detailed_tab:
    st.subheader("Detailed Project Schedule")
    st.caption("Task-level schedule organized by work section.")

    if filtered_df.empty:
        st.info("No tasks match the current filters.")
    else:
        detailed_fig = create_gantt(filtered_df, "Project Schedule")
        st.plotly_chart(
            detailed_fig,
            use_container_width=True,
            config={
                "displaylogo": False,
                "responsive": True,
                "scrollZoom": False,
            },
        )

with team_tab:
    st.subheader("Individual Team Schedule")

    if not all_members:
        st.info("No team members were found in the Owners column.")
    else:
        team_member = st.selectbox(
            "Select team member",
            options=all_members,
            key="team_view_member",
        )

        member_df = df[
            df["Owners"].apply(lambda owners: team_member in owners)
        ].copy()

        if member_df.empty:
            st.info(f"No tasks are currently assigned to {team_member}.")
        else:
            m1, m2, m3 = st.columns(3)
            member_completed = int((member_df["PercentComplete"] >= 100).sum())
            member_progress = float(member_df["PercentComplete"].mean())

            m1.metric("Assigned tasks", len(member_df))
            m2.metric("Completed", member_completed)
            m3.metric("Average progress", f"{member_progress:.0f}%")

            member_fig = create_gantt(
                member_df,
                f"{team_member} — Individual Project Schedule",
            )
            st.plotly_chart(
                member_fig,
                use_container_width=True,
                config={
                    "displaylogo": False,
                    "responsive": True,
                    "scrollZoom": False,
                },
            )

with table_tab:
    st.subheader("Project Task Table")
    st.caption("Underlying schedule data from the shared Google Sheet.")

    if filtered_df.empty:
        st.info("No tasks match the current filters.")
    else:
        display_df = filtered_df.copy()
        display_df["Owners"] = display_df["Owners"].apply(", ".join)
        display_df["Start"] = display_df["Start"].dt.strftime("%Y-%m-%d")
        display_df["Finish"] = display_df["Finish"].dt.strftime("%Y-%m-%d")
        display_df["PercentComplete"] = (
            display_df["PercentComplete"].round().astype(int)
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "PercentComplete": st.column_config.ProgressColumn(
                    "Percent complete",
                    min_value=0,
                    max_value=100,
                    format="%d%%",
                ),
                "Milestone": st.column_config.CheckboxColumn("Milestone"),
            },
        )

st.divider()
st.caption(
    "Schedule updates are maintained in the shared Google Sheet. "
    "Use Refresh to retrieve the latest published data."
)
