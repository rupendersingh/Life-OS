import sqlite3
from pathlib import Path


DB_NAME = "life_ops.db"


TASK_COLUMNS = {
    "title": "TEXT",
    "description": "TEXT",
    "due_date": "TEXT",
    "priority": "TEXT DEFAULT 'Medium' CHECK (priority IN ('Low', 'Medium', 'High'))",
    "status": "TEXT DEFAULT 'Pending' CHECK (status IN ('Pending', 'In Progress', 'Done'))",
    "is_top3_for_day": "INTEGER DEFAULT 0 CHECK (is_top3_for_day IN (0, 1))",
    "is_daily_routine": "INTEGER DEFAULT 0 CHECK (is_daily_routine IN (0, 1))",
    "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
}

TASK_MIGRATION_COLUMNS = {
    **TASK_COLUMNS,
    "created_at": "TEXT",
}


def get_connection(db_path: str | Path = DB_NAME) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrate_tasks_table(conn: sqlite3.Connection) -> None:
    existing_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
    }
    for column_name, column_definition in TASK_MIGRATION_COLUMNS.items():
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE tasks ADD COLUMN {column_name} {column_definition}")

    conn.execute("UPDATE tasks SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")


def init_db(db_path: str | Path = DB_NAME) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                title TEXT,
                description TEXT,
                due_date TEXT,
                priority TEXT DEFAULT 'Medium'
                    CHECK (priority IN ('Low', 'Medium', 'High')),
                status TEXT DEFAULT 'Pending'
                    CHECK (status IN ('Pending', 'In Progress', 'Done')),
                is_top3_for_day INTEGER DEFAULT 0
                    CHECK (is_top3_for_day IN (0, 1)),
                is_daily_routine INTEGER DEFAULT 0
                    CHECK (is_daily_routine IN (0, 1)),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT,
                target_hours REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS skill_progress (
                id INTEGER PRIMARY KEY,
                skill_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                hours_spent REAL NOT NULL,
                notes TEXT,
                FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS time_entries (
                id INTEGER PRIMARY KEY,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration_minutes REAL NOT NULL,
                category TEXT NOT NULL,
                notes TEXT,
                task_id INTEGER,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS hr_contacts (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                phone TEXT,
                company TEXT
            );

            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                stage TEXT DEFAULT 'Applied',
                next_step_date TEXT,
                hr_contact_id INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hr_contact_id) REFERENCES hr_contacts(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS email_logs (
                id INTEGER PRIMARY KEY,
                provider TEXT DEFAULT 'Gmail',
                message_id TEXT,
                subject TEXT,
                sender TEXT,
                received_at TEXT,
                snippet TEXT,
                interview_id INTEGER,
                FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS ideas (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT,
                status TEXT DEFAULT 'Backlog',
                impact_estimate REAL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        _migrate_tasks_table(conn)
        conn.commit()
    finally:
        conn.close()
