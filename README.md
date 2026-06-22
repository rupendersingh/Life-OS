# Life Ops Console

Life Ops Console is a personal Python/Streamlit operations dashboard for managing job-search and learning workflows in one place. It is a local, SQLite-backed app intended for daily planning, skill progress, time tracking, interview tracking, and idea backlog management.

## Current Features

- Streamlit app entry point in `app.py` with sidebar navigation for Dashboard, Tasks, Skills, Time Tracking, Interviews, and Ideas.
- SQLite schema initialization and lightweight migrations in `db.py`.
- Data-access helpers in `models.py` for tasks, skills, skill progress, time entries, HR contacts, interviews, email logs, and ideas.
- Dashboard summary for today's Top 3 tasks, task completion count, skill-hours pie chart, and today's time-by-category chart.
- Dashboard upcoming-interview summary for the next 7 days.
- Tasks page with create, edit, delete, mark-done, Top 3 toggle, date filtering, and daily routine cloning.
- Skills page with skill creation, skill editing, progress logging, total-hours summaries, target-hour progress, and dashboard chart data.
- Time Tracking page with time-entry logging, duration validation, today's entries, and category summaries.
- Interviews page with interview creation/editing, HR contact creation, active interview listing, stage updates, HR call-note appending, Gmail HR email fetch, email log display, and email-to-interview linking.
- Ideas page with idea creation, editing, deletion, category/status filtering, impact estimate, notes, and backlog display.
- `debug_db.py` utility for inspecting the local SQLite schema.
- Pytest coverage for task behavior, daily routines, skill progress summaries, time category summaries, active interview filtering, interview notes, upcoming interviews, and email-log linking.

## Tech Stack

- Python 3.11
- Streamlit
- SQLite
- pandas
- matplotlib
- pytest

## Installation

From PowerShell in the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install streamlit pandas matplotlib pytest
```

## Run the App

With the virtual environment activated:

```powershell
python -m streamlit run app.py
```

The app creates `life_ops.db` automatically on startup if it does not already exist.

## Gmail Configuration

Gmail HR email import uses IMAP with environment variables:

```powershell
$env:GMAIL_USERNAME="your.email@gmail.com"
$env:GMAIL_APP_PASSWORD="your-gmail-app-password"
```

Use a Gmail app password rather than your normal account password. If these values are not set, the app shows a friendly setup message instead of fetching Gmail messages.

## Inspect the Database

To print the local SQLite tables and columns:

```powershell
python debug_db.py
```

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

## Roadmap / Next Steps

- Polish Tasks validation and UI details.
- Expand Skills with richer progress history views.
- Expand Time Tracking with optional task linking and richer reporting.
- Polish Interviews with richer HR contact management and closed-interview views.
- Polish Ideas with richer prioritization and reporting.
- Harden Gmail import behavior and add tests around email parsing/storage.
- Expand regression coverage across the full app workflow.

## License

No license has been specified yet.
