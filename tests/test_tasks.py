import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from db import init_db
from models import (
    create_task,
    ensure_daily_routines_for_date,
    get_task,
    list_tasks_for_date,
    update_task,
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


def test_create_task(test_db_path):
    task_id = create_task(
        title="Prepare interview notes",
        description="Review project stories",
        due_date="2026-06-22",
        priority="High",
        db_path=test_db_path,
    )

    task = get_task(task_id, db_path=test_db_path)
    assert task is not None
    assert task["title"] == "Prepare interview notes"
    assert task["description"] == "Review project stories"
    assert task["due_date"] == "2026-06-22"
    assert task["priority"] == "High"
    assert task["status"] == "Pending"
    assert task["is_top3_for_day"] == 0
    assert task["is_daily_routine"] == 0


def test_mark_task_as_done(test_db_path):
    task_id = create_task("Submit application", "2026-06-22", db_path=test_db_path)

    update_task(task_id, db_path=test_db_path, status="Done")

    task = get_task(task_id, db_path=test_db_path)
    assert task["status"] == "Done"


def test_toggle_top3_flag(test_db_path):
    task_id = create_task("Practice coding", "2026-06-22", db_path=test_db_path)

    update_task(task_id, db_path=test_db_path, is_top3_for_day=True)
    task = get_task(task_id, db_path=test_db_path)
    assert task["is_top3_for_day"] == 1

    update_task(task_id, db_path=test_db_path, is_top3_for_day=False)
    task = get_task(task_id, db_path=test_db_path)
    assert task["is_top3_for_day"] == 0


def test_ensure_daily_routines_creates_copies_only_when_needed(test_db_path):
    target_date = "2026-06-22"
    create_task(
        title="Daily planning",
        due_date="2026-06-01",
        priority="High",
        status="Done",
        is_top3_for_day=True,
        is_daily_routine=True,
        db_path=test_db_path,
    )

    created_count = ensure_daily_routines_for_date(target_date, db_path=test_db_path)
    second_created_count = ensure_daily_routines_for_date(target_date, db_path=test_db_path)

    tasks_for_date = list_tasks_for_date(target_date, db_path=test_db_path)
    assert created_count == 1
    assert second_created_count == 0
    assert len(tasks_for_date) == 1

    copied_task = tasks_for_date[0]
    assert copied_task["title"] == "Daily planning"
    assert copied_task["due_date"] == target_date
    assert copied_task["priority"] == "High"
    assert copied_task["status"] == "Pending"
    assert copied_task["is_daily_routine"] == 0
