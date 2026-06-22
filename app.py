import streamlit as st

from db import init_db


PAGES = [
    "Dashboard",
    "Tasks",
    "Skills",
    "Time Tracking",
    "Interviews",
    "Ideas",
]


def show_dashboard() -> None:
    st.title("Dashboard")
    st.write("Today at a glance will show top tasks, task summary, interviews, skills, and time summaries.")


def show_tasks_page() -> None:
    st.title("Tasks")
    st.write("Task planning, Top 3 tasks, daily routines, and task status updates will live here.")


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
