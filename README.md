# Life Ops Console

A personal Streamlit operations console for tasks, skills, time tracking, interviews, HR contacts, email logs, and ideas.

## Setup

From PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install streamlit
```

## Run The App

With the `.venv` activated, run:

```powershell
python -m streamlit run app.py
```

Using `python -m streamlit` makes sure Streamlit runs from the active Python environment.

## Database

The app uses SQLite and creates `life_ops.db` automatically at startup by calling `init_db()`.

## Gmail Integration

Gmail integration is planned for a later implementation pass. Configuration details will be added when `gmail_integration.py` is introduced.
