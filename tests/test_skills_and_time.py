import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from db import init_db
from models import (
    create_skill,
    create_time_entry,
    get_skill_progress_summary,
    get_time_summary_for_date,
    log_skill_progress,
)


@pytest.fixture
def test_db_path():
    test_dir = Path(__file__).parent / ".tmp" / uuid4().hex
    test_dir.mkdir(parents=True, exist_ok=True)
    db_path = test_dir / "life_ops_test.db"
    init_db(db_path)
    try:
        yield db_path
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_skill_progress_summary_totals(test_db_path):
    python_id = create_skill("Python", 100, category="Automation", db_path=test_db_path)
    sql_id = create_skill("SQL", 40, category="Data", db_path=test_db_path)

    log_skill_progress(python_id, "2026-06-22", 1.5, "pytest practice", db_path=test_db_path)
    log_skill_progress(python_id, "2026-06-23", 2.0, "models review", db_path=test_db_path)

    summary = get_skill_progress_summary(db_path=test_db_path)
    print(summary)

    assert summary == [
        {
            "id": python_id,
            "name": "Python",
            "category": "Automation",
            "target_hours": 100.0,
            "total_hours": 3.5,
        },
        {
            "id": sql_id,
            "name": "SQL",
            "category": "Data",
            "target_hours": 40.0,
            "total_hours": 0,
        },
    ]


def test_time_summary_for_date_totals_by_category(test_db_path):
    create_time_entry(
        "2026-06-22 09:00",
        "2026-06-22 10:00",
        60,
        "Deep Work",
        db_path=test_db_path,
    )
    create_time_entry(
        "2026-06-22 10:30",
        "2026-06-22 11:15",
        45,
        "Admin",
        db_path=test_db_path,
    )
    create_time_entry(
        "2026-06-22 14:00",
        "2026-06-22 15:30",
        90,
        "Deep Work",
        db_path=test_db_path,
    )
    create_time_entry(
        "2026-06-23 09:00",
        "2026-06-23 10:00",
        60,
        "Deep Work",
        db_path=test_db_path,
    )

    summary = get_time_summary_for_date("2026-06-22", db_path=test_db_path)
    print(summary)
    assert summary == [
        {"category": "Deep Work", "duration_minutes": 150.0},
        {"category": "Admin", "duration_minutes": 45.0},
    ]
