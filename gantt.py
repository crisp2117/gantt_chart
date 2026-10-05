from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


SECTION_ORDER = [
    "Project Definition",
    "Proposal",
    "Data Acquisition",
    "Data Preparation",
    "Analysis",
    "Visualization",
    "Progress Checkpoint",
    "Final Analysis",
    "Final Deliverables",
]

SECTION_COLORS = {
    "Project Definition": "#2F80ED",
    "Proposal": "#8E5CC7",
    "Data Acquisition": "#219653",
    "Data Preparation": "#2D9CDB",
    "Analysis": "#D9822B",
    "Visualization": "#D64545",
    "Progress Checkpoint": "#3A9D73",
    "Final Analysis": "#8F4CB8",
    "Final Deliverables": "#34495E",
}

HIGH_LEVEL_PHASE_MAP = {
    "Project Definition": "Project Definition & Research",
    "Proposal": "Proposal Development",
    "Data Acquisition": "Data Acquisition",
    "Data Preparation": "Data Preparation & Integration",
    "Analysis": "Analysis & Model Development",
    "Visualization": "Visualization Development",
    "Progress Checkpoint": "Progress Reporting",
    "Final Analysis": "Evaluation & Final Analysis",
    "Final Deliverables": "Final Deliverables",
}

HIGH_LEVEL_PHASE_ORDER = [
    "Project Definition & Research",
    "Proposal Development",
    "Data Acquisition",
    "Data Preparation & Integration",
    "Analysis & Model Development",
    "Visualization Development",
    "Progress Reporting",
    "Evaluation & Final Analysis",
    "Final Deliverables",
]

HIGH_LEVEL_COLORS = {
    HIGH_LEVEL_PHASE_MAP[section]: color
    for section, color in SECTION_COLORS.items()
}

TEXT_PRIMARY = "#1F2937"
TEXT_SECONDARY = "#4B5563"
TEXT_MUTED = "#6B7280"
GRID_COLOR = "#E5E7EB"
TODAY_COLOR = "#C62828"
DEFAULT_COLOR = "#64748B"


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    value = hex_color.lstrip("#")
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _owners_text(value) -> str:
    if isinstance(value, list):
        return ", ".join(value)
    return str(value)


def make_task_label(row: pd.Series) -> str:
    owners = _owners_text(row.get("Owners", []))
    return (
        f"<b>{row['Task']}</b>"
        f"<br><span style='font-size:10px;color:{TEXT_SECONDARY}'>{owners}</span>"
    )


def prepare_gantt_data(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    result["Start"] = pd.to_datetime(result["Start"], errors="coerce")
    result["Finish"] = pd.to_datetime(result["Finish"], errors="coerce")
    result["PercentComplete"] = (
        pd.to_numeric(result["PercentComplete"], errors="coerce")
        .fillna(0)
        .clip(0, 100)
    )
    result = result[
        result["Start"].notna() & result["Finish"].notna()
    ].copy()
    result["Duration"] = result["Finish"] - result["Start"]
    result["CompleteFinish"] = (
        result["Start"]
        + result["Duration"] * (result["PercentComplete"] / 100)
    )
    return result


def _empty_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=dict(text=title, x=0.5),
        height=420,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial", color=TEXT_PRIMARY),
    )
    return fig


def _date_range(data: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    start = data["Start"].min() - pd.Timedelta(days=1)
    # Leave room for completion labels to the right of bars.
    finish = data["Finish"].max() + pd.Timedelta(days=5)
    return start, finish


def _section_list(data: pd.DataFrame) -> list[str]:
    present = data["Section"].dropna().astype(str).unique().tolist()
    ordered = [section for section in SECTION_ORDER if section in present]
    ordered.extend(section for section in present if section not in ordered)
    return ordered


def create_gantt(
    data: pd.DataFrame,
    title: str = "Project Schedule",
) -> go.Figure:
    """Create the detailed, sectioned Gantt chart.

    Layout choices are intentionally conservative:
    - no chart legend (section headers already identify the color grouping)
    - no repeated x-axis title on every subplot
    - Today label is inside the plot area, above the bars
    - each subplot keeps its own readable date ticks
    """
    data = prepare_gantt_data(data)
    if data.empty:
        return _empty_figure(title)

    sections = _section_list(data)
    row_heights = [
        max(len(data[data["Section"] == section]), 1)
        for section in sections
    ]

    # Dynamic spacing: enough separation for date ticks without wasting the page.
    vertical_spacing = min(0.055, 0.28 / max(len(sections), 1))

    fig = make_subplots(
        rows=len(sections),
        cols=1,
        shared_xaxes=False,
        subplot_titles=[f"<b>{section}</b>" for section in sections],
        row_heights=row_heights,
        vertical_spacing=vertical_spacing,
    )

    project_start, project_finish = _date_range(data)
    today = pd.Timestamp.today().normalize()

    for subplot_row, section in enumerate(sections, start=1):
        section_df = data[data["Section"] == section].copy()
        section_color = SECTION_COLORS.get(section, DEFAULT_COLOR)
        baseline_color = hex_to_rgba(section_color, 0.18)
        task_labels: list[str] = []

        for _, task in section_df.iterrows():
            task_label = make_task_label(task)
            task_labels.append(task_label)

            full_duration_ms = (
                (task["Finish"] - task["Start"]).total_seconds() * 1000
            )

            fig.add_trace(
                go.Bar(
                    x=[full_duration_ms],
                    y=[task_label],
                    base=[task["Start"]],
                    orientation="h",
                    width=0.50,
                    marker=dict(
                        color=baseline_color,
                        line=dict(color=section_color, width=1),
                    ),
                    customdata=[[ 
                        _owners_text(task["Owners"]),
                        task["Start"].strftime("%m/%d/%Y"),
                        task["Finish"].strftime("%m/%d/%Y"),
                        int(task["PercentComplete"]),
                        task["Section"],
                    ]],
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Section: %{customdata[4]}<br>"
                        "Owners: %{customdata[0]}<br>"
                        "Start: %{customdata[1]}<br>"
                        "Finish: %{customdata[2]}<br>"
                        "Complete: %{customdata[3]}%"
                        "<extra></extra>"
                    ),
                    showlegend=False,
                ),
                row=subplot_row,
                col=1,
            )

            if task["PercentComplete"] > 0:
                complete_duration_ms = (
                    (task["CompleteFinish"] - task["Start"]).total_seconds()
                    * 1000
                )
                fig.add_trace(
                    go.Bar(
                        x=[complete_duration_ms],
                        y=[task_label],
                        base=[task["Start"]],
                        orientation="h",
                        width=0.50,
                        marker=dict(color=section_color),
                        hoverinfo="skip",
                        showlegend=False,
                    ),
                    row=subplot_row,
                    col=1,
                )

            # Use neutral dark text for completion labels so light section colors
            # never create low-contrast text on the white background.
            fig.add_annotation(
                x=task["Finish"] + pd.Timedelta(hours=8),
                y=task_label,
                text=f"<b>{int(task['PercentComplete'])}%</b>",
                showarrow=False,
                xanchor="left",
                yanchor="middle",
                font=dict(size=11, color=TEXT_PRIMARY),
                row=subplot_row,
                col=1,
            )

        fig.update_yaxes(
            categoryorder="array",
            categoryarray=task_labels,
            autorange="reversed",
            title_text=None,
            tickfont=dict(size=11, color=TEXT_PRIMARY),
            automargin=True,
            row=subplot_row,
            col=1,
        )

        fig.update_xaxes(
            range=[project_start, project_finish],
            type="date",
            tickformat="%b %d",
            dtick=7 * 24 * 60 * 60 * 1000,
            showticklabels=True,
            showgrid=True,
            gridcolor=GRID_COLOR,
            zeroline=False,
            tickfont=dict(size=10, color=TEXT_SECONDARY),
            ticks="outside",
            ticklen=4,
            title_text=None,
            automargin=True,
            row=subplot_row,
            col=1,
        )

        # Today marker: line plus compact label inside the top of each subplot.
        fig.add_vline(
            x=today,
            line_width=1.4,
            line_dash="dash",
            line_color=TODAY_COLOR,
            row=subplot_row,
            col=1,
        )

        if subplot_row == 1:
            xref = "x"
            yref = "y domain"
        else:
            xref = f"x{subplot_row}"
            yref = f"y{subplot_row} domain"

        fig.add_annotation(
            x=today,
            y=0.98,
            xref=xref,
            yref=yref,
            text="Today",
            showarrow=False,
            xanchor="left",
            yanchor="top",
            xshift=4,
            font=dict(size=9, color=TODAY_COLOR),
            bgcolor="rgba(255,255,255,0.85)",
            borderpad=2,
        )

    number_tasks = len(data)
    number_sections = len(sections)
    chart_height = max(
        720,
        58 * number_tasks + 78 * number_sections + 130,
    )

    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            y=0.985,
            xanchor="center",
            yanchor="top",
            font=dict(size=21, color=TEXT_PRIMARY),
        ),
        font=dict(family="Arial", size=12, color=TEXT_PRIMARY),
        barmode="overlay",
        bargap=0.30,
        height=chart_height,
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="closest",
        showlegend=False,
        margin=dict(l=315, r=80, t=82, b=45),
    )

    # make_subplots creates the section headers as annotations.
    # Position them at the left edge of each plotting domain so they don't sit
    # in the same horizontal band as the overall title.
    for annotation in fig.layout.annotations:
        if not annotation.text:
            continue
        clean = annotation.text.replace("<b>", "").replace("</b>", "")
        if clean in sections:
            annotation.update(
                x=0,
                xref="paper",
                xanchor="left",
                font=dict(size=14, color=TEXT_PRIMARY),
            )

    return fig


def create_high_level_gantt(data: pd.DataFrame) -> go.Figure:
    """Create a compact proposal-ready project Gantt."""
    data = prepare_gantt_data(data)
    if data.empty:
        return _empty_figure("High-Level Project Schedule")

    data["HighLevelPhase"] = (
        data["Section"].map(HIGH_LEVEL_PHASE_MAP).fillna(data["Section"])
    )

    rows: list[dict] = []
    for phase in HIGH_LEVEL_PHASE_ORDER:
        phase_df = data[data["HighLevelPhase"] == phase].copy()
        if phase_df.empty:
            continue

        duration_days = phase_df["Duration"].dt.total_seconds() / 86400
        total_duration = duration_days.sum()
        if total_duration > 0:
            completion = (
                (duration_days * phase_df["PercentComplete"]).sum()
                / total_duration
            )
        else:
            completion = phase_df["PercentComplete"].mean()

        rows.append(
            {
                "Phase": phase,
                "Start": phase_df["Start"].min(),
                "Finish": phase_df["Finish"].max(),
                "PercentComplete": completion,
            }
        )

    high_df = pd.DataFrame(rows)
    if high_df.empty:
        return _empty_figure("High-Level Project Schedule")

    high_df["Duration"] = high_df["Finish"] - high_df["Start"]
    high_df["CompleteFinish"] = (
        high_df["Start"]
        + high_df["Duration"] * (high_df["PercentComplete"] / 100)
    )

    fig = go.Figure()
    project_start, project_finish = _date_range(high_df)
    today = pd.Timestamp.today().normalize()

    for _, row in high_df.iterrows():
        color = HIGH_LEVEL_COLORS.get(row["Phase"], DEFAULT_COLOR)
        baseline = hex_to_rgba(color, 0.18)
        full_duration_ms = (
            (row["Finish"] - row["Start"]).total_seconds() * 1000
        )

        fig.add_trace(
            go.Bar(
                x=[full_duration_ms],
                y=[row["Phase"]],
                base=[row["Start"]],
                orientation="h",
                width=0.56,
                marker=dict(
                    color=baseline,
                    line=dict(color=color, width=1.2),
                ),
                customdata=[[ 
                    row["Start"].strftime("%m/%d/%Y"),
                    row["Finish"].strftime("%m/%d/%Y"),
                    int(round(row["PercentComplete"])),
                ]],
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Start: %{customdata[0]}<br>"
                    "Finish: %{customdata[1]}<br>"
                    "Complete: %{customdata[2]}%"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

        if row["PercentComplete"] > 0:
            complete_duration_ms = (
                (row["CompleteFinish"] - row["Start"]).total_seconds() * 1000
            )
            fig.add_trace(
                go.Bar(
                    x=[complete_duration_ms],
                    y=[row["Phase"]],
                    base=[row["Start"]],
                    orientation="h",
                    width=0.56,
                    marker=dict(color=color),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        fig.add_annotation(
            x=row["Finish"] + pd.Timedelta(hours=8),
            y=row["Phase"],
            text=f"<b>{int(round(row['PercentComplete']))}%</b>",
            showarrow=False,
            xanchor="left",
            yanchor="middle",
            font=dict(size=11, color=TEXT_PRIMARY),
        )

    fig.add_vline(
        x=today,
        line_width=1.4,
        line_dash="dash",
        line_color=TODAY_COLOR,
    )
    fig.add_annotation(
        x=today,
        y=1.0,
        xref="x",
        yref="paper",
        text="Today",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
        xshift=4,
        font=dict(size=9, color=TODAY_COLOR),
        bgcolor="rgba(255,255,255,0.85)",
        borderpad=2,
    )

    phase_order = [
        phase
        for phase in HIGH_LEVEL_PHASE_ORDER
        if phase in high_df["Phase"].values
    ]

    fig.update_yaxes(
        categoryorder="array",
        categoryarray=phase_order,
        autorange="reversed",
        title_text=None,
        tickfont=dict(size=11, color=TEXT_PRIMARY),
        automargin=True,
    )

    fig.update_xaxes(
        range=[project_start, project_finish],
        type="date",
        tickformat="%b %d",
        dtick=7 * 24 * 60 * 60 * 1000,
        showgrid=True,
        gridcolor=GRID_COLOR,
        zeroline=False,
        ticks="outside",
        ticklen=4,
        tickfont=dict(size=10, color=TEXT_SECONDARY),
        title_text=None,
        automargin=True,
    )

    fig.update_layout(
        title=dict(
            text="High-Level Project Schedule",
            x=0.5,
            y=0.97,
            xanchor="center",
            yanchor="top",
            font=dict(size=20, color=TEXT_PRIMARY),
        ),
        font=dict(family="Arial", size=12, color=TEXT_PRIMARY),
        barmode="overlay",
        height=max(480, 54 * len(high_df) + 150),
        bargap=0.28,
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        hovermode="closest",
        margin=dict(l=245, r=80, t=70, b=55),
    )

    return fig
