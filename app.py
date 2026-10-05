# ============================================================
# CSE6242 PROJECT GANTT DASHBOARD
# app.py
# ============================================================

from __future__ import annotations

import pandas as pd
import streamlit as st

from data import (
    google_sheet_url,
    load_schedule_from_csv,
    load_schedule_from_google_sheet,
)

from gantt import (
    create_gantt,
    create_high_level_gantt,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Project Gantt Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    h1 {
        margin-bottom: 0.25rem;
    }

    .schedule-source {
        font-size: 0.90rem;
        color: #666666;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD PROJECT SCHEDULE
# ============================================================

@st.cache_data(ttl=30)
def load_schedule():
    """
    Try to load the live published Google Sheet.

    If the Google Sheet cannot be reached,
    fall back to sample_tasks.csv.
    """

    try:

        df = load_schedule_from_google_sheet()

        data_source = "Live Google Sheet"

        error_message = None

    except Exception as exc:

        df = load_schedule_from_csv(
            "sample_tasks.csv"
        )

        data_source = "Local fallback"

        error_message = str(exc)

    return (
        df,
        data_source,
        error_message,
    )


# ============================================================
# REFRESH SCHEDULE
# ============================================================

def refresh_schedule():

    st.cache_data.clear()

    st.rerun()


# ============================================================
# LOAD DATA
# ============================================================

df, data_source, data_error = (
    load_schedule()
)


# ============================================================
# BASIC VALIDATION
# ============================================================

if df.empty:

    st.error(
        "No project schedule data was found."
    )

    st.stop()


# ============================================================
# DERIVED VALUES
# ============================================================

all_members = sorted(
    {
        owner
        for owners in df["Owners"]
        for owner in owners
    }
)


all_sections = (
    df["Section"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)


all_statuses = (
    df["Status"]
    .dropna()
    .astype(str)
    .loc[
        lambda x:
        x.str.strip() != ""
    ]
    .unique()
    .tolist()
)


project_start = (
    df["Start"]
    .min()
)


project_finish = (
    df["Finish"]
    .max()
)


total_tasks = len(
    df
)


completed_tasks = int(
    (
        df["PercentComplete"]
        >= 100
    )
    .sum()
)


average_completion = float(
    df["PercentComplete"]
    .mean()
)


# ============================================================
# PAGE HEADER
# ============================================================

st.title(
    "Project Gantt Dashboard"
)

st.caption(
    "Interactive project schedule and team planning dashboard"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "Schedule controls"
    )

    # --------------------------------------------------------
    # DATA SOURCE
    # --------------------------------------------------------

    st.markdown(
        f"**Data source:** {data_source}"
    )

    if (
        data_source
        == "Local fallback"
        and data_error
    ):

        with st.expander(
            "Why is fallback data being used?"
        ):

            st.code(
                data_error
            )


    # --------------------------------------------------------
    # REFRESH
    # --------------------------------------------------------

    if st.button(
        "Refresh schedule",
        use_container_width=True,
        type="primary",
    ):

        refresh_schedule()


    # --------------------------------------------------------
    # GOOGLE SHEET LINK
    # --------------------------------------------------------

    st.link_button(
        "Open Google Sheet",
        google_sheet_url(),
        use_container_width=True,
    )


    st.divider()


    # ========================================================
    # FILTERS
    # ========================================================

    st.subheader(
        "Filters"
    )


    selected_sections = (
        st.multiselect(
            "Work section",
            options=all_sections,
            default=all_sections,
        )
    )


    if all_statuses:

        selected_statuses = (
            st.multiselect(
                "Status",
                options=all_statuses,
                default=all_statuses,
            )
        )

    else:

        selected_statuses = []


    selected_member = (
        st.selectbox(
            "Team member",
            options=[
                "All Team Members"
            ]
            + all_members,
        )
    )


    st.divider()


    # ========================================================
    # PROJECT SUMMARY
    # ========================================================

    st.subheader(
        "Project summary"
    )

    st.metric(
        "Tasks",
        total_tasks,
    )

    st.metric(
        "Completed",
        completed_tasks,
    )

    st.metric(
        "Average completion",
        f"{average_completion:.0f}%",
    )

    if pd.notna(project_start):

        st.caption(
            "Start: "
            + project_start.strftime(
                "%b %d, %Y"
            )
        )

    if pd.notna(project_finish):

        st.caption(
            "Finish: "
            + project_finish.strftime(
                "%b %d, %Y"
            )
        )


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df.copy()


# ------------------------------------------------------------
# SECTION FILTER
# ------------------------------------------------------------

if selected_sections:

    filtered_df = (
        filtered_df[
            filtered_df["Section"]
            .isin(
                selected_sections
            )
        ]
        .copy()
    )

else:

    filtered_df = (
        filtered_df.iloc[0:0]
        .copy()
    )


# ------------------------------------------------------------
# STATUS FILTER
# ------------------------------------------------------------

if (
    all_statuses
    and selected_statuses
):

    filtered_df = (
        filtered_df[
            filtered_df["Status"]
            .isin(
                selected_statuses
            )
        ]
        .copy()
    )


# ------------------------------------------------------------
# MEMBER FILTER
# ------------------------------------------------------------

if (
    selected_member
    != "All Team Members"
):

    filtered_df = (
        filtered_df[
            filtered_df["Owners"]
            .apply(
                lambda owners:
                selected_member
                in owners
            )
        ]
        .copy()
    )


# ============================================================
# TABS
# ============================================================

(
    overview_tab,
    detailed_tab,
    team_tab,
    table_tab,
) = st.tabs(
    [
        "Overview",
        "Detailed Schedule",
        "Team View",
        "Task Table",
    ]
)


# ============================================================
# OVERVIEW TAB
# ============================================================

with overview_tab:

    st.subheader(
        "High-Level Project Schedule"
    )

    st.caption(
        "Major project phases rolled up from the detailed project schedule."
    )


    if filtered_df.empty:

        st.info(
            "No tasks match the current filters."
        )

    else:

        overview_fig = (
            create_high_level_gantt(
                filtered_df
            )
        )

        st.plotly_chart(
            overview_fig,
            use_container_width=True,
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )


    # --------------------------------------------------------
    # PROJECT METRICS
    # --------------------------------------------------------

    metric_col1, metric_col2, metric_col3, metric_col4 = (
        st.columns(4)
    )


    with metric_col1:

        st.metric(
            "Visible Tasks",
            len(filtered_df),
        )


    with metric_col2:

        visible_completed = int(
            (
                filtered_df[
                    "PercentComplete"
                ]
                >= 100
            )
            .sum()
        )

        st.metric(
            "Completed Tasks",
            visible_completed,
        )


    with metric_col3:

        if not filtered_df.empty:

            visible_completion = float(
                filtered_df[
                    "PercentComplete"
                ]
                .mean()
            )

        else:

            visible_completion = 0

        st.metric(
            "Average Progress",
            f"{visible_completion:.0f}%",
        )


    with metric_col4:

        active_tasks = int(
            (
                (
                    filtered_df[
                        "PercentComplete"
                    ]
                    > 0
                )
                &
                (
                    filtered_df[
                        "PercentComplete"
                    ]
                    < 100
                )
            )
            .sum()
        )

        st.metric(
            "In Progress",
            active_tasks,
        )


# ============================================================
# DETAILED SCHEDULE TAB
# ============================================================

with detailed_tab:

    st.subheader(
        "Detailed Project Schedule"
    )

    st.caption(
        "Full task-level schedule organized by project work section."
    )


    if filtered_df.empty:

        st.info(
            "No tasks match the current filters."
        )

    else:

        detailed_fig = (
            create_gantt(
                filtered_df,
                "Project Schedule",
            )
        )

        st.plotly_chart(
            detailed_fig,
            use_container_width=True,
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )


# ============================================================
# TEAM VIEW TAB
# ============================================================

with team_tab:

    st.subheader(
        "Individual Team Schedule"
    )


    if not all_members:

        st.info(
            "No team members were found "
            "in the Owners column."
        )

    else:

        team_member = (
            st.selectbox(
                "Select team member",
                options=all_members,
                key="team_view_member",
            )
        )


        member_df = (
            df[
                df["Owners"]
                .apply(
                    lambda owners:
                    team_member
                    in owners
                )
            ]
            .copy()
        )


        if member_df.empty:

            st.info(
                f"No tasks are currently "
                f"assigned to {team_member}."
            )

        else:

            # ------------------------------------------------
            # MEMBER METRICS
            # ------------------------------------------------

            member_col1, member_col2, member_col3 = (
                st.columns(3)
            )


            with member_col1:

                st.metric(
                    "Assigned Tasks",
                    len(member_df),
                )


            with member_col2:

                member_completed = int(
                    (
                        member_df[
                            "PercentComplete"
                        ]
                        >= 100
                    )
                    .sum()
                )

                st.metric(
                    "Completed",
                    member_completed,
                )


            with member_col3:

                member_progress = float(
                    member_df[
                        "PercentComplete"
                    ]
                    .mean()
                )

                st.metric(
                    "Average Progress",
                    f"{member_progress:.0f}%",
                )


            # ------------------------------------------------
            # MEMBER GANTT
            # ------------------------------------------------

            member_fig = (
                create_gantt(
                    member_df,
                    (
                        f"{team_member} — "
                        f"Individual Project Schedule"
                    ),
                )
            )

            st.plotly_chart(
                member_fig,
                use_container_width=True,
                config={
                    "displaylogo": False,
                    "responsive": True,
                },
            )


# ============================================================
# TASK TABLE TAB
# ============================================================

with table_tab:

    st.subheader(
        "Project Task Table"
    )

    st.caption(
        "Underlying schedule data from the shared Google Sheet."
    )


    # --------------------------------------------------------
    # PREPARE TABLE FOR DISPLAY
    # --------------------------------------------------------

    display_df = (
        filtered_df.copy()
    )


    if not display_df.empty:

        display_df["Owners"] = (
            display_df["Owners"]
            .apply(
                lambda owners:
                ", ".join(
                    owners
                )
            )
        )


        display_df["Start"] = (
            display_df["Start"]
            .dt.strftime(
                "%Y-%m-%d"
            )
        )


        display_df["Finish"] = (
            display_df["Finish"]
            .dt.strftime(
                "%Y-%m-%d"
            )
        )


        display_df[
            "PercentComplete"
        ] = (
            display_df[
                "PercentComplete"
            ]
            .round()
            .astype(int)
        )


        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "PercentComplete":
                    st.column_config.ProgressColumn(
                        "Percent Complete",
                        min_value=0,
                        max_value=100,
                        format="%d%%",
                    ),

                "Milestone":
                    st.column_config.CheckboxColumn(
                        "Milestone"
                    ),
            },
        )


    else:

        st.info(
            "No tasks match the current filters."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Schedule updates are maintained in the shared Google Sheet. "
    "Use Refresh Schedule to retrieve the latest published data."
)