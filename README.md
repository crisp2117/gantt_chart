# Interactive Project Gantt

A shared project schedule with:

- Google Sheets as the source of truth
- Plotly interactive Gantt charts
- Streamlit hosting
- High-level proposal Gantt
- Detailed sectioned Gantt
- Per-team-member views
- Filters and task table
- Optional in-app editing/write-back

## Google Sheet

The project sheet created for this app is:

https://docs.google.com/spreadsheets/d/12wRNbBQp_JWYK0T8dGAcCnGh3CNiNodI3j7MD__4B1s/edit

The `Tasks` tab uses these columns:

`Task | Section | Start | Finish | Owners | PercentComplete | Status | Priority | Notes | Milestone`

Owners are comma-separated names. Dates should be `YYYY-MM-DD`. Percent complete should be 0-100.

## Recommended workflow

1. Team members edit the Google Sheet.
2. Everyone views the interactive dashboard in Streamlit.
3. Click **Refresh schedule** after changes.
4. Use the Overview tab for proposal/report screenshots.
5. Use Team View for individual schedules.

This keeps editing simple and gives everyone one shared source of truth.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy the secrets template:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Then fill in the Google service-account credentials.

Run:

```bash
streamlit run app.py
```

## Connect the Google Sheet

1. Create a Google Cloud project.
2. Enable **Google Sheets API** and **Google Drive API**.
3. Create a Service Account.
4. Create/download a JSON key.
5. Copy the JSON fields into `.streamlit/secrets.toml` under `[gcp_service_account]`.
6. Share the project Google Sheet with the service account's `client_email`.
   - Viewer is enough if the app only reads.
   - Editor is required for optional in-app write-back.

Do not commit `secrets.toml` to GitHub.

## Streamlit Community Cloud deployment

1. Create a GitHub repository.
2. Push this folder to the repo.
3. Go to Streamlit Community Cloud and create an app from `app.py`.
4. Open the app's **Secrets** settings.
5. Paste the contents of your local `.streamlit/secrets.toml`.
6. Deploy.

Your team can then use the Streamlit URL to view/interact with the Gantt while editing the underlying Google Sheet collaboratively.

## Optional: enable editing from Streamlit

Set:

```toml
[app]
enable_writeback = true
```

The Editor tab will then show a **Save changes to Google Sheets** button.

For a class project, I recommend leaving this `false` at first and having the team edit the Google Sheet directly. It avoids accidental overwrites when multiple people edit at once.

## Proposal image export

The Overview chart is intentionally compact. For a static image in Word, you can add:

```python
fig = create_high_level_gantt(df)
fig.write_image("proposal_gantt.png", width=1600, height=700, scale=2)
```

`kaleido` is already included in `requirements.txt`.
