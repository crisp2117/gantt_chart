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

# Published read-only CSV feed used by the Streamlit app.
CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQMOg4I1V1RXJJyzK_KX5gG2DaHJVh2lmrvOwDlPlsF-dKc0kNLwrxLSDhDCIfKA47hQXSYFw5YgWDk/"
    "pub?gid=391338087&single=true&output=csv"
)

# Editable team sheet. This is separate from the published CSV endpoint.
EDIT_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "12wRNbBQp_JWYK0T8dGAcCnGh3CNiNodI3j7MD__4B1s/edit"
)


def _parse_owners(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if pd.isna(value):
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


def normalize_schedule(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    for column in EXPECTED_COLUMNS:
        if column not in result.columns:
            if column == "PercentComplete":
                result[column] = 0
            elif column == "Milestone":
                result[column] = False
            else:
                result[column] = ""

    result = result[EXPECTED_COLUMNS]
    result["Task"] = result["Task"].astype(str).str.strip()
    result["Section"] = result["Section"].astype(str).str.strip()
    result["Status"] = result["Status"].fillna("").astype(str).str.strip()
    result["Priority"] = result["Priority"].fillna("").astype(str).str.strip()
    result["Notes"] = result["Notes"].fillna("").astype(str)
    result["Start"] = pd.to_datetime(result["Start"], errors="coerce")
    result["Finish"] = pd.to_datetime(result["Finish"], errors="coerce")
    result["PercentComplete"] = (
        pd.to_numeric(result["PercentComplete"], errors="coerce")
        .fillna(0)
        .clip(0, 100)
    )
    result["Owners"] = result["Owners"].apply(_parse_owners)
    result["Milestone"] = (
        result["Milestone"]
        .astype(str)
        .str.lower()
        .isin(["true", "1", "yes", "y"])
    )

    result = result[
        result["Task"].ne("")
        & result["Start"].notna()
        & result["Finish"].notna()
    ].copy()

    return result


def load_schedule_from_google_sheet() -> pd.DataFrame:
    return normalize_schedule(pd.read_csv(CSV_URL))


def load_schedule_from_csv(path: str) -> pd.DataFrame:
    return normalize_schedule(pd.read_csv(path))


def google_sheet_url() -> str:
    return EDIT_SHEET_URL
