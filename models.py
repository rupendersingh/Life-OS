from pathlib import Path
from datetime import date, timedelta
from typing import Any

from db import DB_NAME, get_connection, init_db


TASK_FIELDS = {
    "title",
    "description",
    "due_date",
    "priority",
    "status",
    "is_top3_for_day",
    "is_daily_routine",
    "created_at",
}

SKILL_FIELDS = {
    "name",
    "category",
    "target_hours",
    "created_at",
}

SKILL_PROGRESS_FIELDS = {
    "skill_id",
    "date",
    "hours_spent",
    "notes",
}

TIME_ENTRY_FIELDS = {
    "start_time",
    "end_time",
    "duration_minutes",
    "category",
    "notes",
    "task_id",
}

HR_CONTACT_FIELDS = {
    "name",
    "email",
    "phone",
    "company",
}

INTERVIEW_FIELDS = {
    "company",
    "role",
    "stage",
    "next_step_date",
    "hr_contact_id",
    "notes",
    "created_at",
}

EMAIL_LOG_FIELDS = {
    "provider",
    "message_id",
    "subject",
    "sender",
    "received_at",
    "snippet",
    "interview_id",
}

IDEA_FIELDS = {
    "title",
    "category",
    "status",
    "impact_estimate",
    "notes",
    "created_at",
}


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


def _normalize_task_fields(fields: dict[str, Any]) -> dict[str, Any]:
    invalid_fields = set(fields) - TASK_FIELDS
    if invalid_fields:
        invalid = ", ".join(sorted(invalid_fields))
        raise ValueError(f"Invalid task field(s): {invalid}")

    normalized = dict(fields)
    for flag in ("is_top3_for_day", "is_daily_routine"):
        if flag in normalized and normalized[flag] is not None:
            normalized[flag] = int(bool(normalized[flag]))
    return normalized


def _validate_fields(fields: dict[str, Any], allowed_fields: set[str], label: str) -> dict[str, Any]:
    invalid_fields = set(fields) - allowed_fields
    if invalid_fields:
        invalid = ", ".join(sorted(invalid_fields))
        raise ValueError(f"Invalid {label} field(s): {invalid}")
    return dict(fields)


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


def list_tasks_for_date(
    due_date: str,
    is_top3_for_day: bool | None = None,
    status: str | None = None,
    db_path: str | Path = DB_NAME,
) -> list[dict[str, Any]]:
    query = "SELECT * FROM tasks WHERE due_date = ?"
    params: list[Any] = [due_date]

    if is_top3_for_day is not None:
        query += " AND is_top3_for_day = ?"
        params.append(int(is_top3_for_day))

    if status is not None:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY is_top3_for_day DESC, priority DESC, created_at DESC"
    return _list_rows(query, tuple(params), db_path)


def list_active_top3_tasks_for_date(due_date: str, db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows(
        """
        SELECT *
        FROM tasks
        WHERE due_date = ?
          AND is_top3_for_day = 1
          AND status != 'Done'
        ORDER BY created_at DESC
        """,
        (due_date,),
        db_path,
    )


def list_other_active_tasks_for_date(due_date: str, db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows(
        """
        SELECT *
        FROM tasks
        WHERE due_date = ?
          AND status != 'Done'
          AND is_top3_for_day = 0
        ORDER BY priority DESC, created_at DESC
        """,
        (due_date,),
        db_path,
    )


def list_completed_tasks_for_date(due_date: str, db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows(
        """
        SELECT *
        FROM tasks
        WHERE due_date = ?
          AND status = 'Done'
        ORDER BY created_at DESC
        """,
        (due_date,),
        db_path,
    )


def get_task_completion_summary_for_date(due_date: str, db_path: str | Path = DB_NAME) -> dict[str, int]:
    row = _get_row(
        """
        SELECT
            COUNT(*) AS total_count,
            SUM(CASE WHEN status = 'Done' THEN 1 ELSE 0 END) AS completed_count
        FROM tasks
        WHERE due_date = ?
        """,
        (due_date,),
        db_path,
    )
    return {
        "completed_count": int(row["completed_count"] or 0) if row else 0,
        "total_count": int(row["total_count"] or 0) if row else 0,
    }


def list_top3_tasks_for_date(due_date: str, db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return list_tasks_for_date(due_date, is_top3_for_day=True, db_path=db_path)


def list_tasks_for_date_by_status(
    due_date: str,
    status: str,
    db_path: str | Path = DB_NAME,
) -> list[dict[str, Any]]:
    return list_tasks_for_date(due_date, status=status, db_path=db_path)


def get_task(task_id: int, db_path: str | Path = DB_NAME) -> dict[str, Any] | None:
    return _get_row("SELECT * FROM tasks WHERE id = ?", (task_id,), db_path)


def update_task(task_id: int, db_path: str | Path = DB_NAME, **fields: Any) -> None:
    _update("tasks", task_id, _normalize_task_fields(fields), db_path)


def delete_task(task_id: int, db_path: str | Path = DB_NAME) -> None:
    _delete("tasks", task_id, db_path)


def ensure_daily_routines_for_date(due_date: str, db_path: str | Path = DB_NAME) -> int:
    conn = get_connection(db_path)
    try:
        routine_tasks = conn.execute(
            """
            SELECT title, priority
            FROM tasks
            WHERE is_daily_routine = 1
            ORDER BY created_at ASC
            """
        ).fetchall()

        created_count = 0
        for task in routine_tasks:
            exists = conn.execute(
                """
                SELECT 1
                FROM tasks
                WHERE due_date = ?
                  AND title = ?
                LIMIT 1
                """,
                (due_date, task["title"]),
            ).fetchone()
            if exists:
                continue

            conn.execute(
                """
                INSERT INTO tasks (
                    title,
                    due_date,
                    priority,
                    status,
                    is_daily_routine
                )
                VALUES (?, ?, ?, 'Pending', 0)
                """,
                (
                    task["title"],
                    due_date,
                    task["priority"],
                ),
            )
            created_count += 1

        conn.commit()
        return created_count
    finally:
        conn.close()


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
    _update("skills", skill_id, _validate_fields(fields, SKILL_FIELDS, "skill"), db_path)


def delete_skill(skill_id: int, db_path: str | Path = DB_NAME) -> None:
    _delete("skills", skill_id, db_path)


def log_skill_progress(
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


def create_skill_progress(
    skill_id: int,
    date: str,
    hours_spent: float,
    notes: str | None = None,
    db_path: str | Path = DB_NAME,
) -> int:
    return log_skill_progress(skill_id, date, hours_spent, notes, db_path)


def list_skill_progress(db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows("SELECT * FROM skill_progress ORDER BY date DESC, id DESC", db_path=db_path)


def get_skill_progress(progress_id: int, db_path: str | Path = DB_NAME) -> dict[str, Any] | None:
    return _get_row("SELECT * FROM skill_progress WHERE id = ?", (progress_id,), db_path)


def update_skill_progress(progress_id: int, db_path: str | Path = DB_NAME, **fields: Any) -> None:
    _update(
        "skill_progress",
        progress_id,
        _validate_fields(fields, SKILL_PROGRESS_FIELDS, "skill progress"),
        db_path,
    )


def delete_skill_progress(progress_id: int, db_path: str | Path = DB_NAME) -> None:
    _delete("skill_progress", progress_id, db_path)


def get_skill_progress_summary(db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows(
        """
        SELECT
            skills.id,
            skills.name,
            skills.category,
            skills.target_hours,
            COALESCE(SUM(skill_progress.hours_spent), 0) AS total_hours
        FROM skills
        LEFT JOIN skill_progress
            ON skill_progress.skill_id = skills.id
        GROUP BY skills.id, skills.name, skills.category, skills.target_hours
        ORDER BY skills.name ASC
        """,
        db_path=db_path,
    )


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


def list_time_entries_for_date(entry_date: str, db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows(
        """
        SELECT *
        FROM time_entries
        WHERE substr(start_time, 1, 10) = ?
        ORDER BY start_time DESC
        """,
        (entry_date,),
        db_path,
    )


def get_time_summary_for_date(entry_date: str, db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows(
        """
        SELECT
            category,
            SUM(duration_minutes) AS duration_minutes
        FROM time_entries
        WHERE substr(start_time, 1, 10) = ?
        GROUP BY category
        ORDER BY duration_minutes DESC
        """,
        (entry_date,),
        db_path,
    )


def get_time_entry(entry_id: int, db_path: str | Path = DB_NAME) -> dict[str, Any] | None:
    return _get_row("SELECT * FROM time_entries WHERE id = ?", (entry_id,), db_path)


def update_time_entry(entry_id: int, db_path: str | Path = DB_NAME, **fields: Any) -> None:
    _update("time_entries", entry_id, _validate_fields(fields, TIME_ENTRY_FIELDS, "time entry"), db_path)


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
    _update("hr_contacts", contact_id, _validate_fields(fields, HR_CONTACT_FIELDS, "HR contact"), db_path)


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


def list_active_interviews(db_path: str | Path = DB_NAME) -> list[dict[str, Any]]:
    return _list_rows(
        """
        SELECT
            interviews.*,
            hr_contacts.name AS hr_contact_name,
            hr_contacts.email AS hr_contact_email
        FROM interviews
        LEFT JOIN hr_contacts
            ON hr_contacts.id = interviews.hr_contact_id
        WHERE interviews.stage NOT IN ('Rejected', 'Offer')
        ORDER BY
            CASE WHEN interviews.next_step_date IS NULL THEN 1 ELSE 0 END,
            interviews.next_step_date ASC,
            interviews.created_at DESC
        """,
        db_path=db_path,
    )


def get_interview(interview_id: int, db_path: str | Path = DB_NAME) -> dict[str, Any] | None:
    return _get_row("SELECT * FROM interviews WHERE id = ?", (interview_id,), db_path)


def update_interview(interview_id: int, db_path: str | Path = DB_NAME, **fields: Any) -> None:
    _update("interviews", interview_id, _validate_fields(fields, INTERVIEW_FIELDS, "interview"), db_path)


def append_interview_notes(
    interview_id: int,
    note: str,
    db_path: str | Path = DB_NAME,
) -> None:
    interview = get_interview(interview_id, db_path=db_path)
    if interview is None:
        raise ValueError(f"Interview not found: {interview_id}")

    existing_notes = (interview["notes"] or "").strip()
    new_notes = note.strip()
    combined_notes = f"{existing_notes}\n\n{new_notes}" if existing_notes else new_notes
    update_interview(interview_id, db_path=db_path, notes=combined_notes)


def get_upcoming_interviews(
    db_path: str | Path = DB_NAME,
    today: str | None = None,
    days_ahead: int = 7,
) -> list[dict[str, Any]]:
    target_date = today or date.today().isoformat()
    end_date = (date.fromisoformat(target_date) + timedelta(days=days_ahead)).isoformat()
    return _list_rows(
        """
        SELECT *
        FROM interviews
        WHERE next_step_date BETWEEN ? AND ?
        ORDER BY next_step_date ASC, created_at DESC
        """,
        (target_date, end_date),
        db_path,
    )


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
    _update("email_logs", email_log_id, _validate_fields(fields, EMAIL_LOG_FIELDS, "email log"), db_path)


def link_email_log_to_interview(
    email_log_id: int,
    interview_id: int | None,
    db_path: str | Path = DB_NAME,
) -> None:
    update_email_log(email_log_id, db_path=db_path, interview_id=interview_id)


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


def list_ideas(
    category: str | None = None,
    status: str | None = None,
    db_path: str | Path = DB_NAME,
) -> list[dict[str, Any]]:
    query = "SELECT * FROM ideas WHERE 1 = 1"
    params: list[Any] = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC, id DESC"
    return _list_rows(query, tuple(params), db_path)


def get_idea(idea_id: int, db_path: str | Path = DB_NAME) -> dict[str, Any] | None:
    return _get_row("SELECT * FROM ideas WHERE id = ?", (idea_id,), db_path)


def update_idea(idea_id: int, db_path: str | Path = DB_NAME, **fields: Any) -> None:
    _update("ideas", idea_id, _validate_fields(fields, IDEA_FIELDS, "idea"), db_path)


def delete_idea(idea_id: int, db_path: str | Path = DB_NAME) -> None:
    _delete("ideas", idea_id, db_path)
