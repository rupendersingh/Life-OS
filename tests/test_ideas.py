import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from db import init_db
from models import create_idea, delete_idea, get_idea, list_ideas, update_idea


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


def test_list_ideas_filters_and_sorts_newest_first(test_db_path):
    first_id = create_idea(
        "Build QA dashboard",
        category="Automation Project",
        status="Backlog",
        db_path=test_db_path,
    )
    second_id = create_idea(
        "Practice system design",
        category="Learning",
        status="Next",
        db_path=test_db_path,
    )

    all_ideas = list_ideas(db_path=test_db_path)
    filtered_ideas = list_ideas(category="Learning", status="Next", db_path=test_db_path)

    assert [idea["id"] for idea in all_ideas] == [second_id, first_id]
    assert [idea["id"] for idea in filtered_ideas] == [second_id]


def test_update_and_delete_idea(test_db_path):
    idea_id = create_idea("Old title", status="Backlog", db_path=test_db_path)

    update_idea(
        idea_id,
        title="Updated title",
        status="In Progress",
        impact_estimate=8.5,
        db_path=test_db_path,
    )

    idea = get_idea(idea_id, db_path=test_db_path)
    assert idea["title"] == "Updated title"
    assert idea["status"] == "In Progress"
    assert idea["impact_estimate"] == 8.5

    delete_idea(idea_id, db_path=test_db_path)
    assert get_idea(idea_id, db_path=test_db_path) is None
