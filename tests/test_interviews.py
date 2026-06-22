import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from db import init_db
from models import (
    append_interview_notes,
    create_email_log,
    create_hr_contact,
    create_interview,
    get_email_log,
    get_interview,
    get_upcoming_interviews,
    link_email_log_to_interview,
    list_active_interviews,
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


def test_list_active_interviews_excludes_closed_stages(test_db_path):
    contact_id = create_hr_contact("Priya", "priya@example.com", company="Acme", db_path=test_db_path)
    active_id = create_interview(
        "Acme",
        "QA Lead",
        stage="Technical",
        next_step_date="2026-06-25",
        hr_contact_id=contact_id,
        db_path=test_db_path,
    )
    create_interview("Beta", "SDET", stage="Rejected", db_path=test_db_path)
    create_interview("Gamma", "Automation Lead", stage="Offer", db_path=test_db_path)

    interviews = list_active_interviews(db_path=test_db_path)

    assert len(interviews) == 1
    assert interviews[0]["id"] == active_id
    assert interviews[0]["hr_contact_name"] == "Priya"
    assert interviews[0]["hr_contact_email"] == "priya@example.com"


def test_append_interview_notes_adds_to_existing_notes(test_db_path):
    interview_id = create_interview(
        "Acme",
        "QA Lead",
        notes="Initial screen scheduled.",
        db_path=test_db_path,
    )

    append_interview_notes(interview_id, "Asked about automation framework.", db_path=test_db_path)

    interview = get_interview(interview_id, db_path=test_db_path)
    assert interview["notes"] == "Initial screen scheduled.\n\nAsked about automation framework."


def test_get_upcoming_interviews_limits_to_next_7_days(test_db_path):
    create_interview("Past Co", "SDET", next_step_date="2026-06-21", db_path=test_db_path)
    upcoming_id = create_interview(
        "Acme",
        "QA Lead",
        next_step_date="2026-06-25",
        db_path=test_db_path,
    )
    day_7_id = create_interview(
        "Beta",
        "Automation Lead",
        next_step_date="2026-06-29",
        db_path=test_db_path,
    )
    create_interview("Future Co", "Manager", next_step_date="2026-06-30", db_path=test_db_path)

    interviews = get_upcoming_interviews(today="2026-06-22", db_path=test_db_path)

    assert [interview["id"] for interview in interviews] == [upcoming_id, day_7_id]


def test_link_email_log_to_interview(test_db_path):
    interview_id = create_interview("Acme", "QA Lead", db_path=test_db_path)
    email_log_id = create_email_log(
        subject="Interview discussion",
        sender="hr@acme.com",
        db_path=test_db_path,
    )

    link_email_log_to_interview(email_log_id, interview_id, db_path=test_db_path)

    email_log = get_email_log(email_log_id, db_path=test_db_path)
    assert email_log["interview_id"] == interview_id
