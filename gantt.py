# ============================================================
# CSE6242 PROJECT GANTT DASHBOARD
# gantt.py
# ============================================================

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ============================================================
# SECTION ORDER
# ============================================================

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


# ============================================================
# SECTION COLORS
# ============================================================

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


# ============================================================
# HIGH-LEVEL PHASE MAPPING
# ============================================================

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
    "Project Definition & Research": "#2F80ED",
    "Proposal Development": "#9B51E0",
    "Data Acquisition": "#27AE60",
    "Data Preparation & Integration": "#56CCF2",
    "Analysis & Model Development": "#F2994A",
    "Visualization Development": "#EB5757",
    "Progress Reporting": "#6FCF97",
    "Evaluation & Final Analysis": "#BB6BD9",
    "Final Deliverables": "#34495E",
}


# ============================================================
# TEXT COLORS
# ============================================================

TEXT_PRIMARY = "#222222"
TEXT_SECONDARY = "#444444"
TEXT_DARK = "#111111"
GRID_COLOR = "#E5E5E5"


# ============================================================
# HELPERS
# ============================================================

def hex_to_rgba(
    hex_color: str,
    alpha: float,
) -> str:

    hex_color = hex_color.lstrip("#")

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return (
        f"rgba("
        f"{r},"
        f"{g},"
        f"{b},"
        f"{alpha}"
        f")"
    )


def make_task_label(
    row: pd.Series,
) -> str:

    owners = row.get(
        "Owners",
        [],
    )

    if isinstance(owners, list):
        owners_text = ", ".join(owners)
    else:
        owners_text = str(owners)

    return (
        f"<b>{row['Task']}</b>"
        f"<br>"
        f"<span style='font-size:10px;color:{TEXT_SECONDARY}'>"
        f"{owners_text}"
        f"</span>"
    )


def prepare_gantt_data(
    data: pd.DataFrame,
) -> pd.DataFrame:

    data = data.copy()

    data["Start"] = pd.to_datetime(
        data["Start"],
        errors="coerce",
    )

    data["Finish"] = pd.to_datetime(
        data["Finish"],
        errors="coerce",
    )

    data["PercentComplete"] = (
        pd.to_numeric(
            data["PercentComplete"],
            errors="coerce",
        )
        .fillna(0)
        .clip(0, 100)
    )

    data = (
        data[
            data["Start"].notna()
            &
            data["Finish"].notna()
        ]
        .copy()
    )

    data["Duration"] = (
        data["Finish"]
        - data["Start"]
    )

    data["CompleteFinish"] = (
        data["Start"]
        +
        data["Duration"]
        *
        (
            data["PercentComplete"]
            / 100
        )
    )

    return data


# ============================================================
# DETAILED GANTT
# ============================================================

def create_gantt(
    data: pd.DataFrame,
    title: str = "Project Schedule",
) -> go.Figure:

    data = prepare_gantt_data(
        data
    )

    if data.empty:

        fig = go.Figure()

        fig.update_layout(
            title=title,
            height=500,
            font=dict(
                color=TEXT_PRIMARY,
            ),
        )

        return fig


    # --------------------------------------------------------
    # SECTIONS PRESENT IN CURRENT DATA
    # --------------------------------------------------------

    sections = [
        section
        for section in SECTION_ORDER
        if section in data["Section"].unique()
    ]


    unknown_sections = [
        section
        for section in data["Section"].dropna().unique()
        if section not in sections
    ]

    sections.extend(
        unknown_sections
    )


    # --------------------------------------------------------
    # ROW HEIGHTS
    # --------------------------------------------------------

    row_heights = []

    for section in sections:

        number_tasks = len(
            data[
                data["Section"]
                == section
            ]
        )

        row_heights.append(
            max(
                number_tasks,
                1,
            )
        )


    # --------------------------------------------------------
    # CREATE SUBPLOTS
    # --------------------------------------------------------

    fig = make_subplots(
        rows=len(sections),
        cols=1,
        shared_xaxes=False,
        subplot_titles=[
            f"<b>{section}</b>"
            for section in sections
        ],
        row_heights=row_heights,
        vertical_spacing=0.07,
    )


    # --------------------------------------------------------
    # DATE RANGE
    # --------------------------------------------------------

    project_start = (
        data["Start"].min()
        - pd.Timedelta(
            days=1
        )
    )

    project_finish = (
        data["Finish"].max()
        + pd.Timedelta(
            days=6
        )
    )

    today = (
        pd.Timestamp
        .today()
        .normalize()
    )


    # ========================================================
    # BUILD SECTIONS
    # ========================================================

    for subplot_row, section in enumerate(
        sections,
        start=1,
    ):

        section_df = (
            data[
                data["Section"]
                == section
            ]
            .copy()
        )


        # ----------------------------------------------------
        # COLOR
        # ----------------------------------------------------

        section_color = (
            SECTION_COLORS.get(
                section,
                "#607D8B",
            )
        )

        baseline_color = (
            hex_to_rgba(
                section_color,
                0.20,
            )
        )


        task_labels = []


        # ====================================================
        # TASK BARS
        # ====================================================

        for _, task in section_df.iterrows():

            task_label = make_task_label(
                task
            )

            task_labels.append(
                task_label
            )


            full_duration_ms = (
                (
                    task["Finish"]
                    - task["Start"]
                )
                .total_seconds()
                * 1000
            )


            fig.add_trace(
                go.Bar(
                    x=[
                        full_duration_ms
                    ],

                    y=[
                        task_label
                    ],

                    base=[
                        task["Start"]
                    ],

                    orientation="h",

                    width=0.55,

                    marker=dict(
                        color=baseline_color,
                        line=dict(
                            color=section_color,
                            width=1,
                        ),
                    ),

                    customdata=[[
                        ", ".join(
                            task["Owners"]
                        )
                        if isinstance(
                            task["Owners"],
                            list,
                        )
                        else str(
                            task["Owners"]
                        ),

                        task["Start"].strftime(
                            "%m/%d/%Y"
                        ),

                        task["Finish"].strftime(
                            "%m/%d/%Y"
                        ),

                        int(
                            task[
                                "PercentComplete"
                            ]
                        ),

                        task[
                            "Section"
                        ],
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


            # ------------------------------------------------
            # COMPLETED PORTION
            # ------------------------------------------------

            if (
                task[
                    "PercentComplete"
                ]
                > 0
            ):

                complete_duration_ms = (
                    (
                        task[
                            "CompleteFinish"
                        ]
                        - task[
                            "Start"
                        ]
                    )
                    .total_seconds()
                    * 1000
                )


                fig.add_trace(
                    go.Bar(
                        x=[
                            complete_duration_ms
                        ],

                        y=[
                            task_label
                        ],

                        base=[
                            task[
                                "Start"
                            ]
                        ],

                        orientation="h",

                        width=0.55,

                        marker=dict(
                            color=section_color,
                        ),

                        hoverinfo="skip",

                        showlegend=False,
                    ),

                    row=subplot_row,
                    col=1,
                )


            # ------------------------------------------------
            # PERCENT COMPLETE LABEL
            # ------------------------------------------------

            percent_x = (
                task["Finish"]
                + pd.Timedelta(
                    hours=8
                )
            )


            fig.add_annotation(
                x=percent_x,

                y=task_label,

                text=(
                    f"<b>"
                    f"{int(task['PercentComplete'])}%"
                    f"</b>"
                ),

                showarrow=False,

                xanchor="left",

                yanchor="middle",

                font=dict(
                    size=11,
                    color=section_color,
                ),

                row=subplot_row,
                col=1,
            )


        # ====================================================
        # Y AXIS
        # ====================================================

        fig.update_yaxes(
            categoryorder="array",

            categoryarray=task_labels,

            autorange="reversed",

            title="",

            tickfont=dict(
                size=11,
                color=TEXT_PRIMARY,
            ),

            row=subplot_row,
            col=1,
        )


        # ====================================================
        # X AXIS
        # ====================================================

        fig.update_xaxes(
            range=[
                project_start,
                project_finish,
            ],

            type="date",

            tickformat="%b %d",

            showticklabels=True,

            showgrid=True,

            gridcolor=GRID_COLOR,

            tickfont=dict(
                size=11,
                color=TEXT_PRIMARY,
            ),

            title=dict(
                text="Date",
                font=dict(
                    color=TEXT_PRIMARY,
                    size=11,
                ),
            ),

            title_standoff=4,

            row=subplot_row,
            col=1,
        )


        # ====================================================
        # TODAY LINE
        # ====================================================

        fig.add_vline(
            x=today,

            line_width=1.5,

            line_dash="dash",

            line_color="red",

            row=subplot_row,
            col=1,
        )


        # ====================================================
        # TODAY LABEL
        # ====================================================

        if subplot_row == 1:

            xref = "x"

            yref = "y domain"

        else:

            xref = (
                f"x{subplot_row}"
            )

            yref = (
                f"y{subplot_row} domain"
            )


        fig.add_annotation(
            x=today,

            y=-0.13,

            xref=xref,

            yref=yref,

            text=(
                "Today"
                "<br>"
                + today.strftime(
                    "%-m/%-d/%Y"
                )
            ),

            showarrow=False,

            xanchor="center",

            yanchor="top",

            font=dict(
                size=9,
                color="red",
            ),
        )


    # ========================================================
    # SECTION LEGEND
    # ========================================================

    for section in sections:

        section_color = (
            SECTION_COLORS.get(
                section,
                "#607D8B",
            )
        )


        fig.add_trace(
            go.Scatter(
                x=[
                    None
                ],

                y=[
                    None
                ],

                mode="markers",

                marker=dict(
                    size=11,
                    color=section_color,
                    symbol="square",
                ),

                name=section,

                showlegend=True,
            )
        )


    # ========================================================
    # CHART HEIGHT
    # ========================================================

    number_tasks = len(
        data
    )

    number_sections = len(
        sections
    )


    chart_height = max(
        750,

        (
            72
            * number_tasks
        )
        +
        (
            105
            * number_sections
        )
        +
        160,
    )


    # ========================================================
    # FINAL LAYOUT
    # ========================================================

    fig.update_layout(
        title=dict(
            text=title,

            x=0.5,

            y=0.99,

            xanchor="center",

            yanchor="top",

            font=dict(
                size=22,
                color=TEXT_DARK,
            ),
        ),

        font=dict(
            family="Arial",
            size=12,
            color=TEXT_PRIMARY,
        ),

        barmode="overlay",

        bargap=0.30,

        height=chart_height,

        plot_bgcolor="white",

        paper_bgcolor="white",

        hovermode="closest",

        legend=dict(
            title=dict(
                text="Work Section",
                font=dict(
                    color=TEXT_PRIMARY,
                ),
            ),

            orientation="h",

            x=0.5,

            xanchor="center",

            y=1.01,

            yanchor="bottom",

            font=dict(
                size=10,
                color=TEXT_PRIMARY,
            ),
        ),

        margin=dict(
            l=300,
            r=100,
            t=145,
            b=80,
        ),
    )


    # ========================================================
    # FORMAT SUBPLOT TITLES
    # ========================================================

    for annotation in fig.layout.annotations:

        if (
            annotation.text
            and
            "Today"
            not in annotation.text
        ):

            clean_text = (
                annotation.text
                .replace(
                    "<b>",
                    "",
                )
                .replace(
                    "</b>",
                    "",
                )
            )

            if clean_text in sections:

                annotation.font = dict(
                    size=15,
                    color=TEXT_DARK,
                )


    return fig


# ============================================================
# HIGH-LEVEL PROPOSAL / OVERVIEW GANTT
# ============================================================

def create_high_level_gantt(
    data: pd.DataFrame,
) -> go.Figure:

    data = prepare_gantt_data(
        data
    )


    if data.empty:

        fig = go.Figure()

        fig.update_layout(
            title=(
                "High-Level Project Schedule"
            ),
            height=500,
            font=dict(
                color=TEXT_PRIMARY,
            ),
        )

        return fig


    # --------------------------------------------------------
    # MAP DETAILED SECTIONS TO HIGH-LEVEL PHASES
    # --------------------------------------------------------

    data[
        "HighLevelPhase"
    ] = (
        data["Section"]
        .map(
            HIGH_LEVEL_PHASE_MAP
        )
        .fillna(
            data["Section"]
        )
    )


    # --------------------------------------------------------
    # ROLL UP EACH PHASE
    # --------------------------------------------------------

    high_level_rows = []


    for phase in HIGH_LEVEL_PHASE_ORDER:

        phase_df = (
            data[
                data["HighLevelPhase"]
                == phase
            ]
            .copy()
        )


        if phase_df.empty:

            continue


        phase_start = (
            phase_df["Start"]
            .min()
        )


        phase_finish = (
            phase_df["Finish"]
            .max()
        )


        duration_days = (
            phase_df[
                "Duration"
            ]
            .dt.total_seconds()
            / 86400
        )


        total_duration = (
            duration_days
            .sum()
        )


        if total_duration > 0:

            weighted_completion = (
                (
                    duration_days
                    *
                    phase_df[
                        "PercentComplete"
                    ]
                )
                .sum()
                /
                total_duration
            )

        else:

            weighted_completion = (
                phase_df[
                    "PercentComplete"
                ]
                .mean()
            )


        high_level_rows.append(
            {
                "Phase": phase,
                "Start": phase_start,
                "Finish": phase_finish,
                "PercentComplete": (
                    weighted_completion
                ),
            }
        )


    high_df = pd.DataFrame(
        high_level_rows
    )


    if high_df.empty:

        fig = go.Figure()

        fig.update_layout(
            title=(
                "High-Level Project Schedule"
            ),
            height=500,
            font=dict(
                color=TEXT_PRIMARY,
            ),
        )

        return fig


    # --------------------------------------------------------
    # CALCULATED DURATION
    # --------------------------------------------------------

    high_df[
        "Duration"
    ] = (
        high_df["Finish"]
        - high_df["Start"]
    )


    high_df[
        "CompleteFinish"
    ] = (
        high_df["Start"]
        +
        high_df["Duration"]
        *
        (
            high_df[
                "PercentComplete"
            ]
            / 100
        )
    )


    # --------------------------------------------------------
    # FIGURE
    # --------------------------------------------------------

    fig = go.Figure()


    project_start = (
        high_df["Start"].min()
        - pd.Timedelta(
            days=1
        )
    )


    project_finish = (
        high_df["Finish"].max()
        + pd.Timedelta(
            days=5
        )
    )


    today = (
        pd.Timestamp
        .today()
        .normalize()
    )


    # ========================================================
    # BARS
    # ========================================================

    for _, row in high_df.iterrows():

        color = (
            HIGH_LEVEL_COLORS.get(
                row["Phase"],
                "#607D8B",
            )
        )


        baseline_color = (
            hex_to_rgba(
                color,
                0.20,
            )
        )


        full_duration_ms = (
            (
                row["Finish"]
                - row["Start"]
            )
            .total_seconds()
            * 1000
        )


        # ----------------------------------------------------
        # BASELINE
        # ----------------------------------------------------

        fig.add_trace(
            go.Bar(
                x=[
                    full_duration_ms
                ],

                y=[
                    row["Phase"]
                ],

                base=[
                    row["Start"]
                ],

                orientation="h",

                width=0.58,

                marker=dict(
                    color=baseline_color,
                    line=dict(
                        color=color,
                        width=1.2,
                    ),
                ),

                showlegend=False,

                customdata=[[
                    row[
                        "Start"
                    ].strftime(
                        "%m/%d/%Y"
                    ),

                    row[
                        "Finish"
                    ].strftime(
                        "%m/%d/%Y"
                    ),

                    int(
                        round(
                            row[
                                "PercentComplete"
                            ]
                        )
                    ),
                ]],

                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Start: %{customdata[0]}<br>"
                    "Finish: %{customdata[1]}<br>"
                    "Complete: %{customdata[2]}%"
                    "<extra></extra>"
                ),
            )
        )


        # ----------------------------------------------------
        # COMPLETED PORTION
        # ----------------------------------------------------

        if (
            row[
                "PercentComplete"
            ]
            > 0
        ):

            complete_duration_ms = (
                (
                    row[
                        "CompleteFinish"
                    ]
                    - row[
                        "Start"
                    ]
                )
                .total_seconds()
                * 1000
            )


            fig.add_trace(
                go.Bar(
                    x=[
                        complete_duration_ms
                    ],

                    y=[
                        row["Phase"]
                    ],

                    base=[
                        row["Start"]
                    ],

                    orientation="h",

                    width=0.58,

                    marker=dict(
                        color=color,
                    ),

                    showlegend=False,

                    hoverinfo="skip",
                )
            )


        # ----------------------------------------------------
        # PERCENT LABEL
        # ----------------------------------------------------

        fig.add_annotation(
            x=(
                row["Finish"]
                + pd.Timedelta(
                    hours=10
                )
            ),

            y=row["Phase"],

            text=(
                f"<b>"
                f"{int(round(row['PercentComplete']))}%"
                f"</b>"
            ),

            showarrow=False,

            xanchor="left",

            yanchor="middle",

            font=dict(
                size=12,
                color=color,
            ),
        )


    # ========================================================
    # TODAY LINE
    # ========================================================

    fig.add_vline(
        x=today,

        line_width=1.5,

        line_dash="dash",

        line_color="red",
    )


    fig.add_annotation(
        x=today,

        y=-0.11,

        xref="x",

        yref="paper",

        text=(
            "Today"
            "<br>"
            + today.strftime(
                "%-m/%-d/%Y"
            )
        ),

        showarrow=False,

        xanchor="center",

        yanchor="top",

        font=dict(
            size=10,
            color="red",
        ),
    )


    # ========================================================
    # AXES
    # ========================================================

    phase_order = [
        phase
        for phase in HIGH_LEVEL_PHASE_ORDER
        if phase
        in high_df[
            "Phase"
        ].values
    ]


    fig.update_yaxes(
        categoryorder="array",

        categoryarray=phase_order,

        autorange="reversed",

        title="",

        tickfont=dict(
            size=12,
            color=TEXT_PRIMARY,
        ),
    )


    fig.update_xaxes(
        range=[
            project_start,
            project_finish,
        ],

        type="date",

        tickformat="%b %d",

        dtick=(
            7
            * 24
            * 60
            * 60
            * 1000
        ),

        showgrid=True,

        gridcolor=GRID_COLOR,

        tickfont=dict(
            size=11,
            color=TEXT_PRIMARY,
        ),

        title=dict(
            text="Project Timeline",
            font=dict(
                size=11,
                color=TEXT_PRIMARY,
            ),
        ),

        title_standoff=8,
    )


    # ========================================================
    # FINAL LAYOUT
    # ========================================================

    fig.update_layout(
        title=dict(
            text=(
                "High-Level Project Schedule"
            ),

            x=0.5,

            y=0.98,

            xanchor="center",

            yanchor="top",

            font=dict(
                size=20,
                color=TEXT_DARK,
            ),
        ),

        font=dict(
            family="Arial",
            size=12,
            color=TEXT_PRIMARY,
        ),

        barmode="overlay",

        height=620,

        bargap=0.28,

        plot_bgcolor="white",

        paper_bgcolor="white",

        margin=dict(
            l=230,
            r=90,
            t=80,
            b=90,
        ),

        hovermode="closest",
    )


    return fig