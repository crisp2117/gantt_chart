from __future__ import annotations

from typing import Any

import pandas as pd


EXPECTED_COLUMNS = [
    "Task",
    "Section",
    "Start",
    "Finish",
    "Owners",
    "PercentComplete",
    "Status",
    "Priority",
    "Notes",
    "Milestone",
]


# ============================================================
# GOOGLE SHEET CONFIG
# ============================================================



CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/e/2PACX-1vQMOg4I1V1RXJJyzK_KX5gG2DaHJVh2lmrvOwDlPlsF-dKc0kNLwrxLSDhDCIfKA47hQXSYFw5YgWDk/pub?gid=391338087&single=true&output=csv"
)


# ============================================================
# HELPERS
# ============================================================

def _parse_owners(value: Any) -> list[str]:

    if isinstance(value, list):
        return [
            str(x).strip()
            for x in value
            if str(x).strip()
        ]

    if pd.isna(value):
        return []

    return [
        x.strip()
        for x in str(value).split(",")
        if x.strip()
    ]


def normalize_schedule(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = df.copy()

    # --------------------------------------------------------
    # MAKE SURE ALL EXPECTED COLUMNS EXIST
    # --------------------------------------------------------

    for col in EXPECTED_COLUMNS:

        if col not in df.columns:

            if col == "PercentComplete":
                df[col] = 0

            elif col == "Milestone":
                df[col] = False

            else:
                df[col] = ""

    df = df[EXPECTED_COLUMNS]

    # --------------------------------------------------------
    # CLEAN DATA
    # --------------------------------------------------------

    df["Task"] = (
        df["Task"]
        .astype(str)
        .str.strip()
    )

    df["Section"] = (
        df["Section"]
        .astype(str)
        .str.strip()
    )

    df["Start"] = pd.to_datetime(
        df["Start"],
        errors="coerce"
    )

    df["Finish"] = pd.to_datetime(
        df["Finish"],
        errors="coerce"
    )

    df["PercentComplete"] = (
        pd.to_numeric(
            df["PercentComplete"],
            errors="coerce"
        )
        .fillna(0)
        .clip(0, 100)
    )

    df["Owners"] = (
        df["Owners"]
        .apply(_parse_owners)
    )

    df["Milestone"] = (
        df["Milestone"]
        .astype(str)
        .str.lower()
        .isin([
            "true",
            "1",
            "yes",
            "y",
        ])
    )

    # --------------------------------------------------------
    # REMOVE INVALID ROWS
    # --------------------------------------------------------

    df = df[
        df["Task"].ne("")
        &
        df["Start"].notna()
        &
        df["Finish"].notna()
    ].copy()

    return df


# ============================================================
# LOAD LIVE GOOGLE SHEET
# ============================================================

def load_schedule_from_google_sheet() -> pd.DataFrame:

    df = pd.read_csv(
        CSV_URL
    )

    return normalize_schedule(
        df
    )


# ============================================================
# LOCAL CSV FALLBACK
# ============================================================

def load_schedule_from_csv(
    path: str
) -> pd.DataFrame:

    return normalize_schedule(
        pd.read_csv(path)
    )


# ============================================================
# GOOGLE SHEET LINK
# ============================================================

def google_sheet_url() -> str:

    return (
        f"https://docs.google.com/spreadsheets/d/e/2PACX-1vQMOg4I1V1RXJJyzK_KX5gG2DaHJVh2lmrvOwDlPlsF-dKc0kNLwrxLSDhDCIfKA47hQXSYFw5YgWDk/edit"
    )