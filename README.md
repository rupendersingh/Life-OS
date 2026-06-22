# Life Ops Console

Life Ops Console is a personal Python/Streamlit operations dashboard for managing job-search and learning workflows in one place. The project is currently scaffolded as a portfolio-quality SQLite-backed app, with task management implemented first and the remaining Life-OS domains planned from the product spec.

## Current Features

- Streamlit app entry point in `app.py` with sidebar navigation for Dashboard, Tasks, Skills, Time Tracking, Interviews, and Ideas.
- SQLite schema initialization and lightweight migrations in `db.py`.
- Data-access helpers in `models.py` for tasks, skills, skill progress, time entries, HR contacts, interviews, email logs, and ideas.
- Dashboard summary for today's Top 3 tasks and task completion count.
- Tasks page with create, edit, delete, mark-done, Top 3 toggle, date filtering, and daily routine cloning.
- `debug_db.py` utility for inspecting the local SQLite schema.
- Pytest coverage focused on task behavior.
- Skills, Time Tracking, Interviews, Ideas, and Gmail/HR email workflows are planned and partially scaffolded at the database/model level.

## Tech Stack

- Python 3.11
- Streamlit
- SQLite
- pytest

## Installation

From PowerShell in the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install streamlit pytest
```

## Run the App

With the virtual environment activated:

```powershell
python -m streamlit run app.py
```

The app creates `life_ops.db` automatically on startup if it does not already exist.

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

- Complete the Skills page with skill management, progress logging, progress bars, and charts.
- Complete Time Tracking with time-entry forms, duration calculation, and category summaries.
- Complete Interviews with HR contacts, interview stages, notes, and upcoming interview views.
- Complete Ideas with backlog entry, filtering, and status tracking.
- Add Gmail-based HR email import and linking to interviews.
- Expand tests for skills, time tracking, interviews, ideas, and end-to-end regression flows.

## License

No license has been specified yet.
