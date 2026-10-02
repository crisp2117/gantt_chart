import os
from pathlib import Path

import pandas as pd
import streamlit as st

from data import (
    google_sheet_url,
    load_schedule_from_csv,
    load_schedule_from_google_sheet,
    normalize_schedule,
    save_schedule_to_google_sheet,
)
from gantt import create_detailed_gantt, create_high_level_gantt

st.set_page_config(
    page_title="Project Schedule",
    page_icon="📅",
    layout="wide",
)

st.title("Project Schedule")
st.caption("Shared, interactive Gantt dashboard powered by Google Sheets + Plotly.")


@st.cache_data(ttl=60)
def load_data() -> tuple[pd.DataFrame, str]:
    try:
        return load_schedule_from_google_sheet(), "Google Sheets"
    except Exception as exc:
        fallback = Path(__file__).parent / "sample_tasks.csv"
        if fallback.exists():
            return load_schedule_from_csv(str(fallback)), f"Local fallback ({exc})"
        raise


def refresh():
    st.cache_data.clear()
    st.rerun()


df, source = load_data()

with st.sidebar:
    st.header("Schedule controls")
    st.write(f"**Data source:** {source}")
    if st.button("↻ Refresh schedule", use_container_width=True):
        refresh()

    source_url = google_sheet_url()
    if source_url:
        st.link_button("Open Google Sheet", source_url, use_container_width=True)

    all_members = sorted({owner for owners in df["Owners"] for owner in owners})
    all_sections = sorted(df["Section"].dropna().unique().tolist())
    all_statuses = sorted([x for x in df["Status"].dropna().unique().tolist() if str(x).strip()])

    member_filter = st.selectbox("Team member", ["All"] + all_members)
    section_filter = st.selectbox("Section", ["All"] + all_sections)
    status_filter = st.selectbox("Status", ["All"] + all_statuses)

filtered = df.copy()
if member_filter != "All":
    filtered = filtered[filtered["Owners"].apply(lambda owners: member_filter in owners)]
if section_filter != "All":
    filtered = filtered[filtered["Section"] == section_filter]
if status_filter != "All":
    filtered = filtered[filtered["Status"] == status_filter]

# Summary metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Tasks", len(filtered))
m2.metric("Average complete", f"{filtered['PercentComplete'].mean():.0f}%" if len(filtered) else "0%")
m3.metric("In progress", int((filtered["Status"] == "In Progress").sum()))
m4.metric("Complete", int((filtered["PercentComplete"] >= 100).sum()))

overview_tab, detailed_tab, team_tab, table_tab, editor_tab = st.tabs(
    ["Overview", "Detailed Schedule", "Team View", "Task Table", "Editor"]
)

with overview_tab:
    st.subheader("High-Level Project Schedule")
    st.plotly_chart(create_high_level_gantt(filtered if len(filtered) else df), use_container_width=True)
    st.caption("This is the compact view intended for proposal/report screenshots or exports.")

with detailed_tab:
    st.subheader("Detailed Project Gantt")
    if filtered.empty:
        st.info("No tasks match the selected filters.")
    else:
        st.plotly_chart(create_detailed_gantt(filtered, "Detailed Project Schedule"), use_container_width=True)

with team_tab:
    team_member = st.selectbox("Choose team member", all_members, key="team_tab_member")
    member_df = df[df["Owners"].apply(lambda owners: team_member in owners)].copy()
    st.plotly_chart(
        create_detailed_gantt(member_df, f"{team_member} — Individual Project Schedule"),
        use_container_width=True,
    )

with table_tab:
    display = df.copy()
    display["Owners"] = display["Owners"].apply(lambda x: ", ".join(x))
    display["Start"] = display["Start"].dt.date
    display["Finish"] = display["Finish"].dt.date
    st.dataframe(display, use_container_width=True, hide_index=True)

with editor_tab:
    st.markdown("### Schedule Editor")
    st.caption(
        "Recommended workflow: edit the shared Google Sheet directly. "
        "Optional write-back from this app can also be enabled."
    )

    editable = df.copy()
    editable["Owners"] = editable["Owners"].apply(lambda x: ", ".join(x))

    edited = st.data_editor(
        editable,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Start": st.column_config.DateColumn("Start"),
            "Finish": st.column_config.DateColumn("Finish"),
            "PercentComplete": st.column_config.NumberColumn("% Complete", min_value=0, max_value=100, step=5),
            "Milestone": st.column_config.CheckboxColumn("Milestone"),
            "Status": st.column_config.SelectboxColumn(
                "Status", options=["Not Started", "In Progress", "Blocked", "Complete"]
            ),
            "Priority": st.column_config.SelectboxColumn(
                "Priority", options=["Low", "Medium", "High"]
            ),
        },
        key="schedule_editor",
    )

    writeback_enabled = False
    try:
        writeback_enabled = bool(st.secrets.get("app", {}).get("enable_writeback", False))
    except Exception:
        writeback_enabled = os.getenv("ENABLE_WRITEBACK", "false").lower() == "true"

    if writeback_enabled:
        if st.button("Save changes to Google Sheets", type="primary"):
            try:
                to_save = normalize_schedule(edited)
                save_schedule_to_google_sheet(to_save)
                st.success("Changes saved to Google Sheets.")
                st.cache_data.clear()
            except Exception as exc:
                st.error(f"Could not save changes: {exc}")
    else:
        st.info(
            "Write-back is disabled by default. Team members can update the Google Sheet, "
            "then click Refresh schedule. See README.md to enable in-app saving."
        )
