from datetime import date

import streamlit as st

from db import init_db
from models import (
    create_task,
    delete_task,
    ensure_daily_routines_for_date,
    get_task_completion_summary_for_date,
    list_active_top3_tasks_for_date,
    list_completed_tasks_for_date,
    list_other_active_tasks_for_date,
    update_task,
)


PAGES = [
    "Dashboard",
    "Tasks",
    "Skills",
    "Time Tracking",
    "Interviews",
    "Ideas",
]

PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["Pending", "In Progress", "Done"]


def show_dashboard() -> None:
    st.title("Dashboard")

    today_text = date.today().isoformat()
    top3_tasks = list_active_top3_tasks_for_date(today_text)
    task_summary = get_task_completion_summary_for_date(today_text)

    st.subheader("Today's Top 3 Tasks")
    if top3_tasks:
        for task in top3_tasks:
            st.write(f"- {task['title']} ({task['priority']})")
    else:
        st.caption("No active Top 3 tasks for today.")

    st.write(
        f"{task_summary['completed_count']} of "
        f"{task_summary['total_count']} tasks completed for today"
    )


def show_tasks_page() -> None:
    st.title("Tasks")

    selected_date = st.date_input("Date", value=date.today())
    selected_date_text = selected_date.isoformat()
    created_routines = ensure_daily_routines_for_date(selected_date_text)
    if created_routines:
        st.info(f"Created {created_routines} daily routine task(s) for this date.")

    show_create_task_form(selected_date_text)

    top3_tasks = list_active_top3_tasks_for_date(selected_date_text)
    other_tasks = list_other_active_tasks_for_date(selected_date_text)
    completed_tasks = list_completed_tasks_for_date(selected_date_text)

    show_task_section("Top 3 tasks for this date", top3_tasks)
    show_task_section("Other tasks for this date", other_tasks)
    show_task_section("Completed tasks for this date", completed_tasks)


def show_create_task_form(selected_date_text: str) -> None:
    st.subheader("Create task")
    with st.form("create_task_form", clear_on_submit=True):
        title = st.text_input("Title")
        description = st.text_area("Description")
        priority = st.selectbox("Priority", PRIORITIES, index=1)
        status = st.selectbox("Status", STATUSES)
        is_top3_for_day = st.checkbox("Top 3 task")
        is_daily_routine = st.checkbox("Daily routine")
        submitted = st.form_submit_button("Create task")

    if submitted:
        if not title.strip():
            st.error("Title is required.")
            return

        create_task(
            title=title.strip(),
            description=description.strip() or None,
            due_date=selected_date_text,
            priority=priority,
            status=status,
            is_top3_for_day=is_top3_for_day,
            is_daily_routine=is_daily_routine,
        )
        st.success("Task created.")
        st.rerun()


def show_task_section(title: str, tasks: list[dict]) -> None:
    st.subheader(title)
    if not tasks:
        st.caption("No tasks in this section.")
        return

    for task in tasks:
        show_task_item(task)


def show_task_item(task: dict) -> None:
    task_id = task["id"]
    heading = f"{task['title']} · {task['priority']} · {task['status']}"
    with st.expander(heading):
        if task.get("description"):
            st.write(task["description"])
        st.caption(
            f"Due: {task['due_date']} | "
            f"Top 3: {yes_no(task['is_top3_for_day'])} | "
            f"Daily routine: {yes_no(task['is_daily_routine'])}"
        )

        action_cols = st.columns(3)
        with action_cols[0]:
            if task["status"] != "Done" and st.button("Mark Done", key=f"done_{task_id}"):
                update_task(task_id, status="Done")
                st.rerun()
        with action_cols[1]:
            top3_label = "Remove Top 3" if task["is_top3_for_day"] else "Make Top 3"
            if st.button(top3_label, key=f"top3_{task_id}"):
                update_task(task_id, is_top3_for_day=not bool(task["is_top3_for_day"]))
                st.rerun()
        with action_cols[2]:
            if st.button("Delete", key=f"delete_{task_id}"):
                delete_task(task_id)
                st.rerun()

        show_edit_task_form(task)


def show_edit_task_form(task: dict) -> None:
    task_id = task["id"]
    with st.form(f"edit_task_{task_id}"):
        st.markdown("**Edit task**")
        title = st.text_input("Title", value=task["title"] or "", key=f"title_{task_id}")
        description = st.text_area(
            "Description",
            value=task["description"] or "",
            key=f"description_{task_id}",
        )
        priority = st.selectbox(
            "Priority",
            PRIORITIES,
            index=index_or_default(PRIORITIES, task["priority"], 1),
            key=f"priority_{task_id}",
        )
        status = st.selectbox(
            "Status",
            STATUSES,
            index=index_or_default(STATUSES, task["status"], 0),
            key=f"status_{task_id}",
        )
        is_top3_for_day = st.checkbox(
            "Top 3 task",
            value=bool(task["is_top3_for_day"]),
            key=f"edit_top3_{task_id}",
        )
        is_daily_routine = st.checkbox(
            "Daily routine",
            value=bool(task["is_daily_routine"]),
            key=f"edit_routine_{task_id}",
        )
        submitted = st.form_submit_button("Save changes")

    if submitted:
        if not title.strip():
            st.error("Title is required.")
            return

        update_task(
            task_id,
            title=title.strip(),
            description=description.strip() or None,
            priority=priority,
            status=status,
            is_top3_for_day=is_top3_for_day,
            is_daily_routine=is_daily_routine,
        )
        st.success("Task updated.")
        st.rerun()


def index_or_default(options: list[str], value: str | None, default: int = 0) -> int:
    return options.index(value) if value in options else default


def yes_no(value: int | bool) -> str:
    return "Yes" if bool(value) else "No"


def show_skills_page() -> None:
    st.title("Skills")
    st.write("Skill goals, progress logging, progress bars, and skill charts will live here.")


def show_time_tracking_page() -> None:
    st.title("Time Tracking")
    st.write("Time entry logging, daily totals, and category summaries will live here.")


def show_interviews_page() -> None:
    st.title("Interviews")
    st.write("Interview tracking, HR contacts, call notes, and email logs will live here.")


def show_ideas_page() -> None:
    st.title("Ideas")
    st.write("Project ideas, filters, and backlog management will live here.")


def main() -> None:
    st.set_page_config(page_title="Life Ops Console", layout="wide")
    init_db()

    st.sidebar.title("Life Ops Console")
    selected_page = st.sidebar.radio("Navigate", PAGES)

    page_renderers = {
        "Dashboard": show_dashboard,
        "Tasks": show_tasks_page,
        "Skills": show_skills_page,
        "Time Tracking": show_time_tracking_page,
        "Interviews": show_interviews_page,
        "Ideas": show_ideas_page,
    }
    page_renderers[selected_page]()


if __name__ == "__main__":
    main()
