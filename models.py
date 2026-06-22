from pathlib import Path
from typing import Any

from db import DB_NAME, get_connection, init_db


def initialize_db(db_path: str | Path = DB_NAME) -> None:
    init_db(db_path)


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row)


def _list_rows(query: str, params: tuple[Any, ...] = (), db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()
    return [_row_to_dict(row) for row in rows]


def _get_row(query: str, params: tuple[Any, ...], db_path: str | Path = DB_NAME) -> dict[str, Any] | None:
    conn = get_connection(db_path)
    try:
        row = conn.execute(query, params).fetchone()
    finally:
        conn.close()
    return _row_to_dict(row) if row else None


def _execute(query: str, params: tuple[Any, ...], db_path: str | Path = DB_NAME) -> int:
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _update(table: str, record_id: int, fields: dict[str, Any], db_path: str | Path = DB_NAME) -> None:
    if not fields:
        return
    assignments = ", ".join(f"{column} = ?" for column in fields)
    params = tuple(fields.values()) + (record_id,)
    _execute(f"UPDATE {table} SET {assignments} WHERE id = ?", params, db_path)


def _delete(table: str, record_id: int, db_path: str | Path = DB_NAME) -> None:
    _execute(f"DELETE FROM {table} WHERE id = ?", (record_id,), db_path)


def create_task(
    title: str,
    due_date: str,
    description: str | None = None,
    priority: str = "Medium",
    status: str = "Pending",
    is_top3_for_day: bool = False,
    is_daily_routine: bool = False,
    db_path: str | Path = DB_NAME,
) -> int:
    return _execute(
        """
        INSERT INTO tasks (
            title, description, due_date, priority, status, is_top3_for_day, is_daily_routine
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (title, description, due_date, priority, status, int(is_top3_for_day), int(is_daily_routine)),
        db_path,
    )


def list_tasks(db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows("SELECT * FROM tasks ORDER BY due_date ASC, created_at DESC", db_path=db_path)


def get_task(task_id: int, db_path: str | Path = DB_NAME) -> dict[str, Any] | None:
    return _get_row("SELECT * FROM tasks WHERE id = ?", (task_id,), db_path)


def update_task(task_id: int, db_path: str | Path = DB_NAME, **fields: Any) -> None:
    _update("tasks", task_id, fields, db_path)


def delete_task(task_id: int, db_path: str | Path = DB_NAME) -> None:
    _delete("tasks", task_id, db_path)


def create_skill(
    name: str,
    target_hours: float,
    category: str | None = None,
    db_path: str | Path = DB_NAME,
) -> int:
    return _execute(
        "INSERT INTO skills (name, category, target_hours) VALUES (?, ?, ?)",
        (name, category, target_hours),
        db_path,
    )


def list_skills(db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows("SELECT * FROM skills ORDER BY name ASC", db_path=db_path)


def get_skill(skill_id: int, db_path: str | Path = DB_NAME) -> dict[str, Any] | None:
    return _get_row("SELECT * FROM skills WHERE id = ?", (skill_id,), db_path)


def update_skill(skill_id: int, db_path: str | Path = DB_NAME, **fields: Any) -> None:
    _update("skills", skill_id, fields, db_path)


def delete_skill(skill_id: int, db_path: str | Path = DB_NAME) -> None:
    _delete("skills", skill_id, db_path)


def create_skill_progress(
    skill_id: int,
    date: str,
    hours_spent: float,
    notes: str | None = None,
    db_path: str | Path = DB_NAME,
) -> int:
    return _execute(
        "INSERT INTO skill_progress (skill_id, date, hours_spent, notes) VALUES (?, ?, ?, ?)",
        (skill_id, date, hours_spent, notes),
        db_path,
    )


def list_skill_progress(db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows("SELECT * FROM skill_progress ORDER BY date DESC, id DESC", db_path=db_path)


def get_skill_progress(progress_id: int, db_path: str | Path = DB_NAME) -> dict[str, Any] | None:
    return _get_row("SELECT * FROM skill_progress WHERE id = ?", (progress_id,), db_path)


def update_skill_progress(progress_id: int, db_path: str | Path = DB_NAME, **fields: Any) -> None:
    _update("skill_progress", progress_id, fields, db_path)


def delete_skill_progress(progress_id: int, db_path: str | Path = DB_NAME) -> None:
    _delete("skill_progress", progress_id, db_path)


def create_time_entry(
    start_time: str,
    end_time: str,
    duration_minutes: float,
    category: str,
    notes: str | None = None,
    task_id: int | None = None,
    db_path: str | Path = DB_NAME,
) -> int:
    return _execute(
        """
        INSERT INTO time_entries (start_time, end_time, duration_minutes, category, notes, task_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (start_time, end_time, duration_minutes, category, notes, task_id),
        db_path,
    )


def list_time_entries(db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows("SELECT * FROM time_entries ORDER BY start_time DESC", db_path=db_path)


def get_time_entry(entry_id: int, db_path: str | Path = DB_NAME) -> dict[str, Any] | None:
    return _get_row("SELECT * FROM time_entries WHERE id = ?", (entry_id,), db_path)


def update_time_entry(entry_id: int, db_path: str | Path = DB_NAME, **fields: Any) -> None:
    _update("time_entries", entry_id, fields, db_path)


def delete_time_entry(entry_id: int, db_path: str | Path = DB_NAME) -> None:
    _delete("time_entries", entry_id, db_path)


def create_hr_contact(
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    company: str | None = None,
    db_path: str | Path = DB_NAME,
) -> int:
    return _execute(
        "INSERT INTO hr_contacts (name, email, phone, company) VALUES (?, ?, ?, ?)",
        (name, email, phone, company),
        db_path,
    )


def list_hr_contacts(db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows("SELECT * FROM hr_contacts ORDER BY company ASC, name ASC", db_path=db_path)


def get_hr_contact(contact_id: int, db_path: str | Path = DB_NAME) -> dict[str, Any] | None:
    return _get_row("SELECT * FROM hr_contacts WHERE id = ?", (contact_id,), db_path)


def update_hr_contact(contact_id: int, db_path: str | Path = DB_NAME, **fields: Any) -> None:
    _update("hr_contacts", contact_id, fields, db_path)


def delete_hr_contact(contact_id: int, db_path: str | Path = DB_NAME) -> None:
    _delete("hr_contacts", contact_id, db_path)


def create_interview(
    company: str,
    role: str,
    stage: str = "Applied",
    next_step_date: str | None = None,
    hr_contact_id: int | None = None,
    notes: str | None = None,
    db_path: str | Path = DB_NAME,
) -> int:
    return _execute(
        """
        INSERT INTO interviews (company, role, stage, next_step_date, hr_contact_id, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (company, role, stage, next_step_date, hr_contact_id, notes),
        db_path,
    )


def list_interviews(db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows("SELECT * FROM interviews ORDER BY next_step_date ASC, created_at DESC", db_path=db_path)


def get_interview(interview_id: int, db_path: str | Path = DB_NAME) -> dict[str, Any] | None:
    return _get_row("SELECT * FROM interviews WHERE id = ?", (interview_id,), db_path)


def update_interview(interview_id: int, db_path: str | Path = DB_NAME, **fields: Any) -> None:
    _update("interviews", interview_id, fields, db_path)


def delete_interview(interview_id: int, db_path: str | Path = DB_NAME) -> None:
    _delete("interviews", interview_id, db_path)


def create_email_log(
    provider: str = "Gmail",
    message_id: str | None = None,
    subject: str | None = None,
    sender: str | None = None,
    received_at: str | None = None,
    snippet: str | None = None,
    interview_id: int | None = None,
    db_path: str | Path = DB_NAME,
) -> int:
    return _execute(
        """
        INSERT INTO email_logs (
            provider, message_id, subject, sender, received_at, snippet, interview_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (provider, message_id, subject, sender, received_at, snippet, interview_id),
        db_path,
    )


def list_email_logs(db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows("SELECT * FROM email_logs ORDER BY received_at DESC, id DESC", db_path=db_path)


def get_email_log(email_log_id: int, db_path: str | Path = DB_NAME) -> dict[str, Any] | None:
    return _get_row("SELECT * FROM email_logs WHERE id = ?", (email_log_id,), db_path)


def update_email_log(email_log_id: int, db_path: str | Path = DB_NAME, **fields: Any) -> None:
    _update("email_logs", email_log_id, fields, db_path)


def delete_email_log(email_log_id: int, db_path: str | Path = DB_NAME) -> None:
    _delete("email_logs", email_log_id, db_path)


def create_idea(
    title: str,
    category: str | None = None,
    status: str = "Backlog",
    impact_estimate: float | None = None,
    notes: str | None = None,
    db_path: str | Path = DB_NAME,
) -> int:
    return _execute(
        "INSERT INTO ideas (title, category, status, impact_estimate, notes) VALUES (?, ?, ?, ?, ?)",
        (title, category, status, impact_estimate, notes),
        db_path,
    )


def list_ideas(db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows("SELECT * FROM ideas ORDER BY created_at DESC", db_path=db_path)


def get_idea(idea_id: int, db_path: str | Path = DB_NAME) -> dict[str, Any] | None:
    return _get_row("SELECT * FROM ideas WHERE id = ?", (idea_id,), db_path)


def update_idea(idea_id: int, db_path: str | Path = DB_NAME, **fields: Any) -> None:
    _update("ideas", idea_id, fields, db_path)


def delete_idea(idea_id: int, db_path: str | Path = DB_NAME) -> None:
    _delete("ideas", idea_id, db_path)
