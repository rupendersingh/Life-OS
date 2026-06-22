from datetime import date, datetime, time

import pandas as pd
import streamlit as st

from db import init_db
from gmail_integration import fetch_recent_hr_emails, store_email_logs
from models import (
    append_interview_notes,
    create_hr_contact,
    create_idea,
    create_interview,
    create_skill,
    create_task,
    create_time_entry,
    delete_idea,
    delete_task,
    ensure_daily_routines_for_date,
    get_skill_progress_summary,
    get_task_completion_summary_for_date,
    get_time_summary_for_date,
    get_upcoming_interviews,
    link_email_log_to_interview,
    list_active_interviews,
    list_active_top3_tasks_for_date,
    list_completed_tasks_for_date,
    list_email_logs,
    list_hr_contacts,
    list_ideas,
    list_interviews,
    list_other_active_tasks_for_date,
    list_skills,
    list_time_entries_for_date,
    log_skill_progress,
    update_skill,
    update_task,
    update_interview,
    update_idea,
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
INTERVIEW_STAGES = ["Applied", "HR Screen", "Technical", "Final", "Offer", "Rejected"]
IDEA_STATUSES = ["Backlog", "Next", "In Progress", "Done", "Dropped"]
IDEA_CATEGORIES = ["Career", "Learning", "Automation Project"]


def show_dashboard() -> None:
    st.title("Dashboard")

    today_text = date.today().isoformat()
    top3_tasks = list_active_top3_tasks_for_date(today_text)
    task_summary = get_task_completion_summary_for_date(today_text)
    skill_summaries = get_skill_progress_summary()
    time_summary = get_time_summary_for_date(today_text)
    upcoming_interviews = get_upcoming_interviews(today=today_text)

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

    st.subheader("Skill hours by skill")
    skill_hours = [
        {"skill": row["name"], "hours": row["total_hours"]}
        for row in skill_summaries
        if row["total_hours"] > 0
    ]
    if skill_hours:
        st.pyplot(create_pie_chart(skill_hours, "skill", "hours"))
    else:
        st.caption("No skill progress logged yet.")

    st.subheader("Today's time by category")
    category_minutes = [
        {"category": row["category"], "minutes": row["duration_minutes"]}
        for row in time_summary
        if row["duration_minutes"] > 0
    ]
    if category_minutes:
        st.bar_chart(
            pd.DataFrame(category_minutes).set_index("category"),
            y="minutes",
        )
    else:
        st.caption("No time entries logged today.")

    st.subheader("Upcoming Interviews")
    if upcoming_interviews:
        st.dataframe(
            [
                {
                    "Company": interview["company"],
                    "Role": interview["role"],
                    "Stage": interview["stage"],
                    "Next step date": interview["next_step_date"],
                }
                for interview in upcoming_interviews
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No interviews scheduled in the next 7 days.")


def create_pie_chart(rows: list[dict], label_key: str, value_key: str):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    labels = [row[label_key] for row in rows]
    values = [row[value_key] for row in rows]
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    return fig


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

    show_create_skill_form()

    skills = list_skills()
    show_log_skill_progress_form(skills)
    show_skill_progress_list()


def show_create_skill_form() -> None:
    st.subheader("Add skill")
    with st.form("create_skill_form", clear_on_submit=True):
        name = st.text_input("Name")
        category = st.text_input("Category")
        target_hours = st.number_input("Target hours", min_value=0.0, step=1.0, value=10.0)
        submitted = st.form_submit_button("Add skill")

    if submitted:
        if not name.strip():
            st.error("Skill name is required.")
            return

        create_skill(
            name=name.strip(),
            category=category.strip() or None,
            target_hours=target_hours,
        )
        st.success("Skill added.")
        st.rerun()


def show_log_skill_progress_form(skills: list[dict]) -> None:
    st.subheader("Log progress")
    if not skills:
        st.caption("Add a skill before logging progress.")
        return

    with st.form("log_skill_progress_form", clear_on_submit=True):
        selected_skill = st.selectbox(
            "Skill",
            skills,
            format_func=lambda skill: skill["name"],
        )
        progress_date = st.date_input("Date", value=date.today())
        hours_spent = st.number_input("Hours spent", min_value=0.0, step=0.25, value=1.0)
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Log progress")

    if submitted:
        if hours_spent <= 0:
            st.error("Hours spent must be greater than zero.")
            return

        log_skill_progress(
            skill_id=selected_skill["id"],
            date=progress_date.isoformat(),
            hours_spent=hours_spent,
            notes=notes.strip() or None,
        )
        st.success("Progress logged.")
        st.rerun()


def show_skill_progress_list() -> None:
    st.subheader("Skill progress")
    summaries = get_skill_progress_summary()

    if not summaries:
        st.caption("No skills yet.")
        return

    for skill in summaries:
        show_skill_progress_item(skill)


def show_skill_progress_item(skill: dict) -> None:
    skill_id = skill["id"]
    target_hours = float(skill["target_hours"] or 0)
    total_hours = float(skill["total_hours"] or 0)
    progress = min(total_hours / target_hours, 1.0) if target_hours else 0.0

    with st.expander(skill["name"]):
        cols = st.columns([2, 1, 1, 2])
        cols[0].write(skill["category"] or "Uncategorized")
        cols[1].metric("Total hours", f"{total_hours:g}")
        cols[2].metric("Target hours", f"{target_hours:g}")
        cols[3].progress(progress)

        with st.form(f"edit_skill_{skill_id}"):
            st.markdown("**Edit skill**")
            name = st.text_input("Name", value=skill["name"] or "", key=f"skill_name_{skill_id}")
            category = st.text_input(
                "Category",
                value=skill["category"] or "",
                key=f"skill_category_{skill_id}",
            )
            target = st.number_input(
                "Target hours",
                min_value=0.0,
                step=1.0,
                value=target_hours,
                key=f"skill_target_{skill_id}",
            )
            submitted = st.form_submit_button("Save changes")

        if submitted:
            if not name.strip():
                st.error("Skill name is required.")
                return

            update_skill(
                skill_id,
                name=name.strip(),
                category=category.strip() or None,
                target_hours=target,
            )
            st.success("Skill updated.")
            st.rerun()


def show_time_tracking_page() -> None:
    st.title("Time Tracking")

    show_log_time_entry_form()

    today_text = date.today().isoformat()
    entries = list_time_entries_for_date(today_text)
    summary = get_time_summary_for_date(today_text)

    st.subheader("Today's entries")
    if entries:
        st.dataframe(
            [
                {
                    "Start": format_datetime(entry["start_time"]),
                    "End": format_datetime(entry["end_time"]),
                    "Minutes": round(float(entry["duration_minutes"] or 0), 2),
                    "Category": entry["category"],
                    "Notes": entry["notes"] or "",
                }
                for entry in entries
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No time entries logged today.")

    st.subheader("Today's category summary")
    if summary:
        summary_rows = [
            {
                "Category": row["category"],
                "Minutes": round(float(row["duration_minutes"] or 0), 2),
                "Hours": round(float(row["duration_minutes"] or 0) / 60, 2),
            }
            for row in summary
        ]
        st.dataframe(summary_rows, use_container_width=True, hide_index=True)
        st.bar_chart(
            [{"category": row["Category"], "minutes": row["Minutes"]} for row in summary_rows],
            x="category",
            y="minutes",
        )
    else:
        st.caption("No category summary yet.")


def show_log_time_entry_form() -> None:
    st.subheader("Log time entry")
    with st.form("log_time_entry_form", clear_on_submit=True):
        start_date = st.date_input("Start date", value=date.today())
        start_clock = st.time_input("Start time", value=time(9, 0))
        end_date = st.date_input("End date", value=date.today())
        end_clock = st.time_input("End time", value=time(10, 0))
        category = st.text_input("Category")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Log time")

    if submitted:
        start_time = datetime.combine(start_date, start_clock)
        end_time = datetime.combine(end_date, end_clock)
        duration_minutes = (end_time - start_time).total_seconds() / 60

        if duration_minutes <= 0:
            st.error("End time must be after start time.")
            return
        if not category.strip():
            st.error("Category is required.")
            return

        create_time_entry(
            start_time=start_time.isoformat(timespec="minutes"),
            end_time=end_time.isoformat(timespec="minutes"),
            duration_minutes=duration_minutes,
            category=category.strip(),
            notes=notes.strip() or None,
        )
        st.success("Time entry logged.")
        st.rerun()


def format_datetime(value: str) -> str:
    return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")


def show_interviews_page() -> None:
    st.title("Interviews")

    contacts = list_hr_contacts()
    show_create_interview_form(contacts)
    show_active_interviews()
    show_hr_email_logs()


def show_create_interview_form(contacts: list[dict]) -> None:
    st.subheader("Create interview")
    contact_mode = st.radio("HR contact", ["Existing", "New"], horizontal=True)

    with st.form("create_interview_form", clear_on_submit=True):
        company = st.text_input("Company")
        role = st.text_input("Role")
        stage = st.selectbox("Stage", INTERVIEW_STAGES)
        next_step_date = st.date_input("Next step date", value=None)

        selected_contact = None
        if contact_mode == "Existing" and contacts:
            selected_contact = st.selectbox(
                "Select HR contact",
                contacts,
                format_func=format_hr_contact,
            )
        elif contact_mode == "Existing":
            st.caption("No HR contacts yet.")
        else:
            contact_name = st.text_input("HR name")
            contact_email = st.text_input("HR email")
            contact_phone = st.text_input("HR phone")

        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Create interview")

    if submitted:
        if not company.strip() or not role.strip():
            st.error("Company and role are required.")
            return

        hr_contact_id = selected_contact["id"] if selected_contact else None
        if contact_mode == "New":
            if not contact_name.strip() and not contact_email.strip():
                st.error("HR name or email is required for a new contact.")
                return
            hr_contact_id = create_hr_contact(
                name=contact_name.strip() or None,
                email=contact_email.strip() or None,
                phone=contact_phone.strip() or None,
                company=company.strip(),
            )

        create_interview(
            company=company.strip(),
            role=role.strip(),
            stage=stage,
            next_step_date=next_step_date.isoformat() if next_step_date else None,
            hr_contact_id=hr_contact_id,
            notes=notes.strip() or None,
        )
        st.success("Interview created.")
        st.rerun()


def show_active_interviews() -> None:
    st.subheader("Active interviews")
    interviews = list_active_interviews()
    if not interviews:
        st.caption("No active interviews.")
        return

    st.dataframe(
        [
            {
                "Company": interview["company"],
                "Role": interview["role"],
                "Stage": interview["stage"],
                "Next step": interview["next_step_date"] or "",
                "HR contact": interview["hr_contact_name"] or interview["hr_contact_email"] or "",
            }
            for interview in interviews
        ],
        use_container_width=True,
        hide_index=True,
    )

    for interview in interviews:
        show_interview_item(interview)


def show_interview_item(interview: dict) -> None:
    interview_id = interview["id"]
    heading = f"{interview['company']} - {interview['role']} - {interview['stage']}"
    with st.expander(heading):
        show_edit_interview_form(interview)

        cols = st.columns(2)
        with cols[0]:
            if st.button("Rejected", key=f"reject_interview_{interview_id}"):
                update_interview(interview_id, stage="Rejected")
                st.rerun()
        with cols[1]:
            if st.button("Offer", key=f"offer_interview_{interview_id}"):
                update_interview(interview_id, stage="Offer")
                st.rerun()

        with st.form(f"call_note_{interview_id}", clear_on_submit=True):
            call_note = st.text_area("HR call note")
            submitted = st.form_submit_button("Append note")

        if submitted:
            if not call_note.strip():
                st.error("Call note is required.")
                return
            append_interview_notes(interview_id, call_note)
            st.success("Call note appended.")
            st.rerun()


def show_hr_email_logs() -> None:
    st.subheader("HR emails")
    if st.button("Fetch latest HR emails from Gmail"):
        try:
            emails = fetch_recent_hr_emails()
            inserted_count = store_email_logs(emails)
        except RuntimeError as error:
            st.error(str(error))
        else:
            st.success(f"Fetched {len(emails)} HR email(s), saved {inserted_count} new log(s).")
            st.rerun()

    email_logs = list_email_logs()
    if not email_logs:
        st.caption("No HR email logs yet.")
        return

    st.dataframe(
        [
            {
                "Received": email_log["received_at"] or "",
                "Sender": email_log["sender"] or "",
                "Subject": email_log["subject"] or "",
                "Snippet": email_log["snippet"] or "",
                "Interview ID": email_log["interview_id"] or "",
            }
            for email_log in email_logs
        ],
        use_container_width=True,
        hide_index=True,
    )

    interviews = list_interviews()
    if not interviews:
        st.caption("Create an interview before linking email logs.")
        return

    interview_options = [None] + interviews
    for email_log in email_logs:
        show_email_log_link_form(email_log, interview_options)


def show_email_log_link_form(email_log: dict, interview_options: list[dict | None]) -> None:
    email_log_id = email_log["id"]
    selected_index = next(
        (
            index
            for index, interview in enumerate(interview_options)
            if interview and interview["id"] == email_log["interview_id"]
        ),
        0,
    )

    with st.form(f"link_email_log_{email_log_id}"):
        st.caption(f"{email_log['subject'] or '(No subject)'}")
        selected_interview = st.selectbox(
            "Interview",
            interview_options,
            index=selected_index,
            format_func=format_interview_option,
            key=f"email_interview_{email_log_id}",
        )
        submitted = st.form_submit_button("Link to interview")

    if submitted:
        if selected_interview is None:
            st.error("Select an interview before linking.")
            return

        link_email_log_to_interview(email_log_id, selected_interview["id"])
        st.success("Email linked to interview.")
        st.rerun()


def show_edit_interview_form(interview: dict) -> None:
    interview_id = interview["id"]
    contacts = list_hr_contacts()
    contact_options = [None] + contacts
    selected_contact_index = next(
        (
            index
            for index, contact in enumerate(contact_options)
            if contact and contact["id"] == interview["hr_contact_id"]
        ),
        0,
    )

    with st.form(f"edit_interview_{interview_id}"):
        st.markdown("**Edit interview**")
        company = st.text_input("Company", value=interview["company"] or "", key=f"company_{interview_id}")
        role = st.text_input("Role", value=interview["role"] or "", key=f"role_{interview_id}")
        stage = st.selectbox(
            "Stage",
            INTERVIEW_STAGES,
            index=index_or_default(INTERVIEW_STAGES, interview["stage"], 0),
            key=f"stage_{interview_id}",
        )
        next_step_date = st.date_input(
            "Next step date",
            value=date.fromisoformat(interview["next_step_date"]) if interview["next_step_date"] else None,
            key=f"next_step_{interview_id}",
        )
        selected_contact = st.selectbox(
            "HR contact",
            contact_options,
            index=selected_contact_index,
            format_func=lambda contact: "None" if contact is None else format_hr_contact(contact),
            key=f"hr_contact_{interview_id}",
        )
        notes = st.text_area("Notes", value=interview["notes"] or "", key=f"notes_{interview_id}")
        submitted = st.form_submit_button("Save changes")

    if submitted:
        if not company.strip() or not role.strip():
            st.error("Company and role are required.")
            return

        update_interview(
            interview_id,
            company=company.strip(),
            role=role.strip(),
            stage=stage,
            next_step_date=next_step_date.isoformat() if next_step_date else None,
            hr_contact_id=selected_contact["id"] if selected_contact else None,
            notes=notes.strip() or None,
        )
        st.success("Interview updated.")
        st.rerun()


def format_hr_contact(contact: dict) -> str:
    name = contact["name"] or "Unnamed"
    company = contact["company"] or "No company"
    email = contact["email"] or "No email"
    return f"{name} ({company}) - {email}"


def format_interview_option(interview: dict | None) -> str:
    if interview is None:
        return "Select interview"
    return f"{interview['company']} - {interview['role']} ({interview['stage']})"


def show_ideas_page() -> None:
    st.title("Ideas")

    show_create_idea_form()

    all_ideas = list_ideas()
    category_options = sorted(
        {idea["category"] for idea in all_ideas if idea["category"]}
        | set(IDEA_CATEGORIES)
    )

    filter_cols = st.columns(2)
    with filter_cols[0]:
        selected_category = st.selectbox("Category filter", ["All"] + category_options)
    with filter_cols[1]:
        selected_status = st.selectbox("Status filter", ["All"] + IDEA_STATUSES)

    ideas = list_ideas(
        category=None if selected_category == "All" else selected_category,
        status=None if selected_status == "All" else selected_status,
    )
    show_ideas_list(ideas)


def show_create_idea_form() -> None:
    st.subheader("Add idea")
    with st.form("create_idea_form", clear_on_submit=True):
        title = st.text_input("Title")
        category = st.text_input("Category")
        status = st.selectbox("Status", IDEA_STATUSES)
        has_impact = st.checkbox("Add impact estimate")
        impact_estimate = st.number_input(
            "Impact estimate",
            min_value=0.0,
            step=0.5,
            value=0.0,
            disabled=not has_impact,
        )
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add idea")

    if submitted:
        if not title.strip():
            st.error("Title is required.")
            return

        create_idea(
            title=title.strip(),
            category=category.strip() or None,
            status=status,
            impact_estimate=impact_estimate if has_impact else None,
            notes=notes.strip() or None,
        )
        st.success("Idea added.")
        st.rerun()


def show_ideas_list(ideas: list[dict]) -> None:
    st.subheader("Backlog")
    if not ideas:
        st.caption("No ideas match these filters.")
        return

    st.dataframe(
        [
            {
                "Title": idea["title"],
                "Category": idea["category"] or "",
                "Status": idea["status"] or "",
                "Impact": idea["impact_estimate"] if idea["impact_estimate"] is not None else "",
                "Created": idea["created_at"] or "",
            }
            for idea in ideas
        ],
        use_container_width=True,
        hide_index=True,
    )

    for idea in ideas:
        show_idea_item(idea)


def show_idea_item(idea: dict) -> None:
    idea_id = idea["id"]
    heading = f"{idea['title']} - {idea['status'] or 'Backlog'}"
    with st.expander(heading):
        if idea["notes"]:
            st.write(idea["notes"])
        st.caption(
            f"Category: {idea['category'] or 'Uncategorized'} | "
            f"Impact: {idea['impact_estimate'] if idea['impact_estimate'] is not None else 'Not set'}"
        )

        if st.button("Delete", key=f"delete_idea_{idea_id}"):
            delete_idea(idea_id)
            st.rerun()

        show_edit_idea_form(idea)


def show_edit_idea_form(idea: dict) -> None:
    idea_id = idea["id"]
    with st.form(f"edit_idea_{idea_id}"):
        st.markdown("**Edit idea**")
        title = st.text_input("Title", value=idea["title"] or "", key=f"idea_title_{idea_id}")
        category = st.text_input("Category", value=idea["category"] or "", key=f"idea_category_{idea_id}")
        status = st.selectbox(
            "Status",
            IDEA_STATUSES,
            index=index_or_default(IDEA_STATUSES, idea["status"], 0),
            key=f"idea_status_{idea_id}",
        )
        has_impact = st.checkbox(
            "Has impact estimate",
            value=idea["impact_estimate"] is not None,
            key=f"idea_has_impact_{idea_id}",
        )
        impact_estimate = st.number_input(
            "Impact estimate",
            min_value=0.0,
            step=0.5,
            value=float(idea["impact_estimate"] or 0),
            disabled=not has_impact,
            key=f"idea_impact_{idea_id}",
        )
        notes = st.text_area("Notes", value=idea["notes"] or "", key=f"idea_notes_{idea_id}")
        submitted = st.form_submit_button("Save changes")

    if submitted:
        if not title.strip():
            st.error("Title is required.")
            return

        update_idea(
            idea_id,
            title=title.strip(),
            category=category.strip() or None,
            status=status,
            impact_estimate=impact_estimate if has_impact else None,
            notes=notes.strip() or None,
        )
        st.success("Idea updated.")
        st.rerun()


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
