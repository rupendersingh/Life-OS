# Repository Guidelines

## Project Structure & Module Organization

This is a Python 3.11 Streamlit app backed by SQLite.

- `app.py` contains the Streamlit entry point, sidebar navigation, and page UI.
- `db.py` owns the SQLite database name, connection setup, schema creation, and migrations.
- `models.py` contains all data-access helpers. UI code should call these helpers instead of writing SQL directly.
- `debug_db.py` is a local schema inspection utility.
- `SPEC.md` is the product/source-of-truth document.
- `tests/` contains pytest tests, currently focused on task behavior.
- Local runtime files such as `.venv/`, `__pycache__/`, `.pytest_cache/`, `tests/.tmp/`, and `life_ops.db` should not be committed.

## Build, Test, and Development Commands

Use PowerShell from the repository root.

```powershell
.\.venv\Scripts\Activate.ps1
python -m streamlit run app.py
```

Runs the local app using the active virtual environment.

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

Runs the pytest suite.

```powershell
python debug_db.py
```

Prints SQLite table names and columns for the local `life_ops.db`.

```powershell
python -m py_compile app.py db.py models.py debug_db.py
```

Performs a quick syntax check.

## Coding Style & Naming Conventions

Use 4-space indentation and standard Python naming: `snake_case` for functions and variables, `UPPER_CASE` for constants. Keep Streamlit UI functions small and page-specific, for example `show_tasks_page()`. Keep database logic in `models.py` or `db.py`; avoid inline SQL in `app.py`.

## Testing Guidelines

Tests use `pytest`. Name test files `test_*.py` and test functions `test_*`. Prefer isolated temporary SQLite databases rather than the real `life_ops.db`. For task tests, follow the existing pattern in `tests/test_tasks.py`, which creates per-test databases under `tests/.tmp` and cleans them up.

## Commit & Pull Request Guidelines

Recent commits use short, imperative summaries such as `Scaffold Life Ops Console` and `Stage 2 completed`. Keep commits focused and avoid mixing app changes with generated runtime files. Pull requests should include a short description, testing performed, screenshots for UI changes when useful, and any schema or migration notes.

## Security & Configuration Tips

Do not commit secrets, Gmail credentials, `.streamlit/secrets.toml`, virtual environments, or local SQLite databases. Keep configuration instructions in `README.md` when new integrations are added.
