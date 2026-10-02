from __future__ import annotations

import os
from typing import Any

import pandas as pd

EXPECTED_COLUMNS = [
    "Task", "Section", "Start", "Finish", "Owners", "PercentComplete",
    "Status", "Priority", "Notes", "Milestone"
]


def _parse_owners(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if pd.isna(value):
        return []
    return [x.strip() for x in str(value).split(",") if x.strip()]


def normalize_schedule(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            if col == "PercentComplete":
                df[col] = 0
            elif col == "Milestone":
                df[col] = False
            else:
                df[col] = ""

    df = df[EXPECTED_COLUMNS]
    df["Task"] = df["Task"].astype(str).str.strip()
    df["Section"] = df["Section"].astype(str).str.strip()
    df["Start"] = pd.to_datetime(df["Start"], errors="coerce")
    df["Finish"] = pd.to_datetime(df["Finish"], errors="coerce")
    df["PercentComplete"] = pd.to_numeric(df["PercentComplete"], errors="coerce").fillna(0).clip(0, 100)
    df["Owners"] = df["Owners"].apply(_parse_owners)
    df["Milestone"] = df["Milestone"].astype(str).str.lower().isin(["true", "1", "yes", "y"])
    df = df[df["Task"].ne("") & df["Start"].notna() & df["Finish"].notna()].copy()
    return df


def _streamlit_secrets():
    try:
        import streamlit as st
        return st.secrets
    except Exception:
        return {}


def get_sheet_config() -> tuple[str | None, str]:
    secrets = _streamlit_secrets()
    sheet_id = None
    worksheet = "Tasks"

    try:
        sheet_id = secrets.get("google", {}).get("sheet_id")
        worksheet = secrets.get("google", {}).get("worksheet", "Tasks")
    except Exception:
        pass

    sheet_id = sheet_id or os.getenv("GOOGLE_SHEET_ID")
    worksheet = os.getenv("GOOGLE_WORKSHEET", worksheet)
    return sheet_id, worksheet


def _gspread_client():
    import gspread
    secrets = _streamlit_secrets()

    try:
        creds = dict(secrets["gcp_service_account"])
        return gspread.service_account_from_dict(creds)
    except Exception:
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path:
            return gspread.service_account(filename=credentials_path)
        raise RuntimeError(
            "Google Sheets credentials are not configured. Add the gcp_service_account "
            "section to .streamlit/secrets.toml or set GOOGLE_APPLICATION_CREDENTIALS."
        )


def load_schedule_from_google_sheet() -> pd.DataFrame:
    sheet_id, worksheet_name = get_sheet_config()
    if not sheet_id:
        raise RuntimeError("GOOGLE_SHEET_ID is not configured.")

    gc = _gspread_client()
    worksheet = gc.open_by_key(sheet_id).worksheet(worksheet_name)
    records = worksheet.get_all_records()
    return normalize_schedule(pd.DataFrame(records))


def load_schedule_from_csv(path: str) -> pd.DataFrame:
    return normalize_schedule(pd.read_csv(path))


def dataframe_for_sheet(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Start"] = pd.to_datetime(out["Start"]).dt.strftime("%Y-%m-%d")
    out["Finish"] = pd.to_datetime(out["Finish"]).dt.strftime("%Y-%m-%d")
    out["Owners"] = out["Owners"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    out["PercentComplete"] = pd.to_numeric(out["PercentComplete"], errors="coerce").fillna(0).clip(0, 100).astype(int)
    out["Milestone"] = out["Milestone"].astype(bool)
    return out[EXPECTED_COLUMNS]


def save_schedule_to_google_sheet(df: pd.DataFrame) -> None:
    sheet_id, worksheet_name = get_sheet_config()
    if not sheet_id:
        raise RuntimeError("GOOGLE_SHEET_ID is not configured.")

    gc = _gspread_client()
    worksheet = gc.open_by_key(sheet_id).worksheet(worksheet_name)
    out = dataframe_for_sheet(normalize_schedule(df))

    values = [out.columns.tolist()] + out.astype(object).where(pd.notna(out), "").values.tolist()
    worksheet.clear()
    worksheet.update(values=values, range_name="A1")


def google_sheet_url() -> str | None:
    sheet_id, _ = get_sheet_config()
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit" if sheet_id else None
