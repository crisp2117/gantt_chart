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
    "Proposal": "#9B51E0",
    "Data Acquisition": "#27AE60",
    "Data Preparation": "#56CCF2",
    "Analysis": "#F2994A",
    "Visualization": "#EB5757",
    "Progress Checkpoint": "#6FCF97",
    "Final Analysis": "#BB6BD9",
    "Final Deliverables": "#34495E",
}

HIGH_LEVEL_PHASES = {
    "Project Definition": "Project Definition & Research",
    "Proposal": "Proposal Development",
    "Data Acquisition": "Data Acquisition",
    "Data Preparation": "Data Preparation & Integration",
    "Analysis": "Analysis & Model Development",
    "Visualization": "Visualization Development",
    "Progress Checkpoint": "Project Checkpoints",
    "Final Analysis": "Evaluation & Final Analysis",
    "Final Deliverables": "Final Deliverables",
}


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    value = hex_color.lstrip("#")
    r, g, b = (int(value[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def _task_label(row: pd.Series, show_owners: bool = True) -> str:
    if not show_owners:
        return f"<b>{row['Task']}</b>"
    owners = ", ".join(row["Owners"]) if isinstance(row["Owners"], list) else str(row["Owners"])
    return (
        f"<b>{row['Task']}</b><br>"
        f"<span style='font-size:10px;color:#777'>{owners}</span>"
    )


def _axis_ref(row_num: int) -> tuple[str, str]:
    if row_num == 1:
        return "x", "y domain"
    return f"x{row_num}", f"y{row_num} domain"


def create_detailed_gantt(data: pd.DataFrame, title: str = "Project Schedule") -> go.Figure:
    data = data.copy()
    sections = [s for s in SECTION_ORDER if s in data["Section"].dropna().unique()]
    if not sections:
        fig = go.Figure()
        fig.update_layout(title=title)
        return fig

    row_heights = [max(len(data[data["Section"] == section]), 1) for section in sections]

    fig = make_subplots(
        rows=len(sections),
        cols=1,
        shared_xaxes=False,
        subplot_titles=[f"<b>{section}</b>" for section in sections],
        row_heights=row_heights,
        vertical_spacing=0.07,
    )

    project_start = data["Start"].min() - pd.Timedelta(days=1)
    project_finish = data["Finish"].max() + pd.Timedelta(days=6)
    today = pd.Timestamp.today().normalize()

    for subplot_row, section in enumerate(sections, start=1):
        section_df = data[data["Section"] == section].copy()
        color = SECTION_COLORS.get(section, "#4C78A8")
        baseline = _hex_to_rgba(color, 0.20)
        labels = []

        for _, task in section_df.iterrows():
            label = _task_label(task, show_owners=True)
            labels.append(label)
            full_ms = (task["Finish"] - task["Start"]).total_seconds() * 1000

            fig.add_trace(
                go.Bar(
                    x=[full_ms],
                    y=[label],
                    base=[task["Start"]],
                    orientation="h",
                    width=0.55,
                    marker=dict(color=baseline, line=dict(color=color, width=1)),
                    customdata=[[
                        ", ".join(task["Owners"]),
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
                        "Complete: %{customdata[3]}%<extra></extra>"
                    ),
                    showlegend=False,
                ),
                row=subplot_row,
                col=1,
            )

            if task["PercentComplete"] > 0:
                complete_finish = task["Start"] + (task["Finish"] - task["Start"]) * (task["PercentComplete"] / 100)
                complete_ms = (complete_finish - task["Start"]).total_seconds() * 1000
                fig.add_trace(
                    go.Bar(
                        x=[complete_ms],
                        y=[label],
                        base=[task["Start"]],
                        orientation="h",
                        width=0.55,
                        marker=dict(color=color),
                        hoverinfo="skip",
                        showlegend=False,
                    ),
                    row=subplot_row,
                    col=1,
                )

            fig.add_annotation(
                x=task["Finish"] + pd.Timedelta(hours=8),
                y=label,
                text=f"<b>{int(task['PercentComplete'])}%</b>",
                showarrow=False,
                xanchor="left",
                yanchor="middle",
                font=dict(size=11, color=color),
                row=subplot_row,
                col=1,
            )

        fig.update_yaxes(
            categoryorder="array",
            categoryarray=labels,
            autorange="reversed",
            title="",
            tickfont=dict(size=11),
            row=subplot_row,
            col=1,
        )

        fig.update_xaxes(
            range=[project_start, project_finish],
            type="date",
            tickformat="%b %d",
            showticklabels=True,
            showgrid=True,
            gridcolor="#EEEEEE",
            title_text="Date",
            title_standoff=4,
            row=subplot_row,
            col=1,
        )

        fig.add_vline(
            x=today,
            line_width=1.5,
            line_dash="dash",
            line_color="red",
            row=subplot_row,
            col=1,
        )

        xref, yref = _axis_ref(subplot_row)
        fig.add_annotation(
            x=today,
            y=-0.13,
            xref=xref,
            yref=yref,
            text="Today<br>" + today.strftime("%-m/%-d/%Y"),
            showarrow=False,
            xanchor="center",
            yanchor="top",
            font=dict(size=9, color="red"),
        )

    for section in sections:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(size=12, color=SECTION_COLORS.get(section, "#4C78A8"), symbol="square"),
                name=section,
                showlegend=True,
            )
        )

    number_tasks = len(data)
    number_sections = len(sections)
    chart_height = max(750, 72 * number_tasks + 105 * number_sections + 180)

    fig.update_layout(
        title=dict(text=title, x=0.5, y=0.99, xanchor="center", yanchor="top", font=dict(size=22)),
        barmode="overlay",
        bargap=0.30,
        height=chart_height,
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="closest",
        legend=dict(
            title=dict(text="Work Section"),
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
        ),
        margin=dict(l=300, r=100, t=145, b=80),
    )

    for annotation in fig.layout.annotations:
        if annotation.text and "Today" not in annotation.text:
            cleaned = annotation.text.replace("<b>", "").replace("</b>", "")
            if cleaned in sections:
                annotation.font = dict(size=15, color="#333333")

    return fig


def build_high_level_dataframe(data: pd.DataFrame) -> pd.DataFrame:
    work = data.copy()
    work["HighLevelPhase"] = work["Section"].map(HIGH_LEVEL_PHASES).fillna(work["Section"])
    work["DurationDays"] = (work["Finish"] - work["Start"]).dt.total_seconds() / 86400
    work["WeightedProgress"] = work["DurationDays"] * work["PercentComplete"]

    grouped = (
        work.groupby("HighLevelPhase", sort=False)
        .agg(
            Start=("Start", "min"),
            Finish=("Finish", "max"),
            DurationDays=("DurationDays", "sum"),
            WeightedProgress=("WeightedProgress", "sum"),
        )
        .reset_index()
    )
    grouped["PercentComplete"] = (
        grouped["WeightedProgress"] / grouped["DurationDays"].replace(0, 1)
    ).round().astype(int)

    phase_order = list(dict.fromkeys(HIGH_LEVEL_PHASES.values()))
    grouped["_order"] = grouped["HighLevelPhase"].apply(lambda x: phase_order.index(x) if x in phase_order else 999)
    return grouped.sort_values("_order").drop(columns=["_order"])


def create_high_level_gantt(data: pd.DataFrame, title: str = "High-Level Project Schedule") -> go.Figure:
    high = build_high_level_dataframe(data)
    fig = go.Figure()
    today = pd.Timestamp.today().normalize()
    project_start = high["Start"].min() - pd.Timedelta(days=1)
    project_finish = high["Finish"].max() + pd.Timedelta(days=4)

    color_cycle = [
        "#2F80ED", "#9B51E0", "#27AE60", "#56CCF2",
        "#F2994A", "#EB5757", "#6FCF97", "#BB6BD9", "#34495E"
    ]

    for idx, row in high.reset_index(drop=True).iterrows():
        color = color_cycle[idx % len(color_cycle)]
        baseline = _hex_to_rgba(color, 0.20)
        full_ms = (row["Finish"] - row["Start"]).total_seconds() * 1000
        fig.add_trace(
            go.Bar(
                x=[full_ms], y=[row["HighLevelPhase"]], base=[row["Start"]], orientation="h", width=0.58,
                marker=dict(color=baseline, line=dict(color=color, width=1.2)), showlegend=False,
                hovertemplate=(
                    f"<b>{row['HighLevelPhase']}</b><br>"
                    f"Start: {row['Start'].strftime('%m/%d/%Y')}<br>"
                    f"Finish: {row['Finish'].strftime('%m/%d/%Y')}<br>"
                    f"Complete: {int(row['PercentComplete'])}%<extra></extra>"
                ),
            )
        )
        if row["PercentComplete"] > 0:
            complete_finish = row["Start"] + (row["Finish"] - row["Start"]) * (row["PercentComplete"] / 100)
            complete_ms = (complete_finish - row["Start"]).total_seconds() * 1000
            fig.add_trace(
                go.Bar(
                    x=[complete_ms], y=[row["HighLevelPhase"]], base=[row["Start"]], orientation="h", width=0.58,
                    marker=dict(color=color), showlegend=False, hoverinfo="skip",
                )
            )
        fig.add_annotation(
            x=row["Finish"] + pd.Timedelta(hours=10), y=row["HighLevelPhase"],
            text=f"<b>{int(row['PercentComplete'])}%</b>", showarrow=False,
            xanchor="left", yanchor="middle", font=dict(size=12, color=color),
        )

    fig.add_vline(x=today, line_width=1.5, line_dash="dash", line_color="red")
    fig.add_annotation(
        x=today, y=-0.10, xref="x", yref="paper",
        text="Today<br>" + today.strftime("%-m/%-d/%Y"), showarrow=False,
        xanchor="center", yanchor="top", font=dict(size=10, color="red"),
    )

    fig.update_yaxes(
        categoryorder="array",
        categoryarray=high["HighLevelPhase"].tolist(),
        autorange="reversed",
        title="",
        tickfont=dict(size=12),
    )
    fig.update_xaxes(
        range=[project_start, project_finish],
        type="date",
        tickformat="%b %d",
        dtick=7 * 24 * 60 * 60 * 1000,
        showgrid=True,
        gridcolor="#EAEAEA",
        title="Project Timeline",
    )
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", font=dict(size=20)),
        barmode="overlay",
        height=560,
        bargap=0.28,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=235, r=90, t=70, b=85),
        font=dict(family="Arial"),
    )
    return fig
