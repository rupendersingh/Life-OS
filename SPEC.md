# Life Ops Console - SPEC

## 1. Overview

**Name:** Life Ops Console

**Purpose:** A single, personal operations console to manage job-search activity, skills, tasks, interviews, time tracking, and ideas. It replaces scattered spreadsheets, notes, and calendars with a focused dashboard.

**User:** Single trusted user. No authentication or multi-tenant support is required for v1.

**High-level goals:**
- Track and plan daily work with a clear "Top 3 tasks for today".
- Track skill-building goals and progress.
- Track interviews, HR contacts, and HR communication.
- Log time spent in learning, planning, job search, and admin work.
- Maintain a backlog of ideas for future projects or initiatives.

The app is for personal use, but it should be structured, tested, and documented as a portfolio-quality project.

---

## 2. Implementation Status

This section records the current state of the codebase and should be updated as implementation progresses.

**Implemented**
- Streamlit app scaffold in `app.py`.
- Sidebar navigation for `Dashboard`, `Tasks`, `Skills`, `Time Tracking`, `Interviews`, and `Ideas`.
- SQLite database setup in `db.py`, including `init_db()` and lightweight task-table migration support.
- SQLite tables for `tasks`, `skills`, `skill_progress`, `time_entries`, `hr_contacts`, `interviews`, `email_logs`, and `ideas`.
- Data-access helpers in `models.py` for the core tables.
- Dashboard support for today's Top 3 tasks, today's task completion summary, skill-hours pie chart, and today's time-by-category chart.
- Dashboard support for upcoming interviews in the next 7 days.
- Initial Tasks page support for creating, editing, deleting, marking done, toggling Top 3, date filtering, and daily routine cloning.
- Initial Skills page support for creating skills, editing skills, logging progress, showing total hours, showing target-hour progress, and providing dashboard chart data.
- Initial Time Tracking page support for logging entries, validating duration, listing today's entries, aggregating today's category totals, and showing category charts.
- Initial Interviews page support for creating and editing interviews, creating HR contacts during interview creation, listing active interviews, updating interview stage, appending HR call notes, displaying HR email logs, and linking email logs to interviews.
- Gmail IMAP integration in `gmail_integration.py` for fetching recent HR-related messages and storing deduplicated `email_logs`.
- Initial Ideas page support for creating, editing, deleting, filtering, and listing ideas.
- `debug_db.py` schema inspection utility.
- Pytest coverage for task behavior, daily routines, skill progress summaries, time category summaries, active interview filtering, interview notes, upcoming interviews, and email-log linking.

**Planned / incomplete**
- Complete Tasks workflow polish and validation.
- Expand `Skills` page behavior with richer progress history and any missing management actions.
- Expand `Time Tracking` page behavior with optional task linking and richer reporting.
- Polish `Interviews` page behavior with richer HR contact management, closed-interview views, and stronger Gmail error/edge-case handling.
- Polish `Ideas` page behavior with richer prioritization and reporting.
- Broader pytest coverage for Gmail parsing/storage, ideas, UI-level flows, and regression flows.

---

## 3. Tech Stack and Architecture

**Runtime and language**
- Python 3.11

**Frontend / UI**
- Streamlit single-page app with sidebar-based navigation.
- `pandas` is used for chart-friendly tabular data in Streamlit.
- `matplotlib` is used for the dashboard skill-hours pie chart.

**Database**
- SQLite single-file database, currently `life_ops.db`.

**App architecture**
- Simple monolith; no microservices.
- `app.py` owns the Streamlit entry point, sidebar navigation, and page UI composition.
- `db.py` owns the SQLite database name, connection setup, schema creation, and migrations.
- `models.py` owns data-access helpers. UI code should call these helpers instead of writing SQL directly.
- `gmail_integration.py` owns Gmail IMAP fetching, HR-message filtering, message parsing, and email-log storage helpers.
- `debug_db.py` is a local schema inspection utility.
- `SPEC.md` is the source of truth for product and technical requirements.
- `tests/` contains pytest tests. Current coverage includes task behavior, daily routines, skill progress summaries, time category summaries, and interview/email-linking behavior.
- No user authentication; assume a trusted local single-user environment.

---

## 4. Core Domains and Data Model

### 4.1 Tasks

Tasks represent actionable items tied to specific dates. Tasks are shown on both the `Dashboard` page and the `Tasks` page.

**Tasks table (`tasks`)**
- `id` (INTEGER, PK)
- `title` (TEXT, required)
- `description` (TEXT, optional)
- `due_date` (TEXT, required) - planned date for the task
- `priority` (TEXT) - one of `Low`, `Medium`, `High`
- `status` (TEXT) - one of `Pending`, `In Progress`, `Done`
- `is_top3_for_day` (INTEGER 0/1) - whether the task is one of the Top 3 tasks for its date
- `is_daily_routine` (INTEGER 0/1) - whether the task is a reusable routine template
- `created_at` (TEXT)

**Current and intended behavior**
- The `Tasks` page has a selected date, defaulting to today.
- Users can create a task for the selected date with title, description, priority, status, Top 3 flag, and daily routine flag.
- Users can edit a task's title, description, priority, status, Top 3 flag, and daily routine flag.
- Users can delete a task.
- Users can mark an active task as `Done`.
- Users can toggle `is_top3_for_day`.
- Daily routine tasks act as templates. When the `Tasks` page loads for a selected date, the app ensures routine tasks exist for that date by cloning missing routine templates.
- The `Tasks` page groups tasks into:
  - Top 3 tasks for this date: `due_date = selected_date`, `is_top3_for_day = 1`, `status != 'Done'`
  - Other tasks for this date: `due_date = selected_date`, `is_top3_for_day = 0`, `status != 'Done'`
  - Completed tasks for this date: `due_date = selected_date`, `status = 'Done'`
- The `Dashboard` page surfaces today's active Top 3 tasks and today's completion summary.

### 4.2 Skills and Skill Progress

Skills represent learning goals. Skill progress represents logged learning sessions against those goals.

**Skills table (`skills`)**
- `id` (INTEGER, PK)
- `name` (TEXT, required)
- `category` (TEXT, optional)
- `target_hours` (REAL, required)
- `created_at` (TEXT)

**Skill progress table (`skill_progress`)**
- `id` (INTEGER, PK)
- `skill_id` (INTEGER, FK to `skills.id`)
- `date` (TEXT)
- `hours_spent` (REAL)
- `notes` (TEXT, optional)

**Intended behavior**
- The `Skills` page allows users to create, edit, and delete skills.
- Each skill has a target number of learning hours.
- Users can log learning sessions by selecting a skill, date, hours spent, and optional notes.
- The app calculates total logged hours per skill from `skill_progress`.
- The `Skills` page shows each skill's total hours, target hours, and progress toward target.
- The `Dashboard` page includes a skill-hours pie chart based on total logged hours per skill.

### 4.3 Time Tracking

Time entries represent blocks of time spent in categories such as learning, planning, job search, and admin work.

**Time entries table (`time_entries`)**
- `id` (INTEGER, PK)
- `start_time` (TEXT)
- `end_time` (TEXT)
- `duration_minutes` (REAL)
- `category` (TEXT)
- `notes` (TEXT, optional)
- `task_id` (INTEGER, optional FK to `tasks.id`)

**Current and intended behavior**
- The `Time Tracking` page allows users to log a time entry with start time, end time, category, and notes.
- Optional task linking through `task_id` is supported by the schema/model layer and remains planned for the UI.
- The app computes and validates `duration_minutes` from start and end time.
- Users can view today's time entries.
- The app aggregates today's time by `category`.
- The `Time Tracking` page shows category totals as a table and simple chart.
- The `Dashboard` page includes today's time summary aggregated by `category`.

### 4.4 Interviews / HR Contacts / Email Logs

Interviews track job opportunities and their stages. HR contacts track people associated with those opportunities. Email logs store HR-related communication, with Gmail as the first provider.

**HR contacts table (`hr_contacts`)**
- `id` (INTEGER, PK)
- `name` (TEXT)
- `email` (TEXT)
- `phone` (TEXT)
- `company` (TEXT)

**Interviews table (`interviews`)**
- `id` (INTEGER, PK)
- `company` (TEXT, required)
- `role` (TEXT, required)
- `stage` (TEXT)
- `next_step_date` (TEXT, optional)
- `hr_contact_id` (INTEGER, optional FK to `hr_contacts.id`)
- `notes` (TEXT, optional)
- `created_at` (TEXT)

**Email logs table (`email_logs`)**
- `id` (INTEGER, PK)
- `provider` (TEXT) - for v1, `Gmail`
- `message_id` (TEXT)
- `subject` (TEXT)
- `sender` (TEXT)
- `received_at` (TEXT)
- `snippet` (TEXT)
- `interview_id` (INTEGER, optional FK to `interviews.id`)

**Current and intended behavior**
- The `Interviews` page allows users to create interviews.
- During interview creation, users can select an existing HR contact or create a new HR contact.
- The `Interviews` page allows users to edit interview company, role, stage, next step date, HR contact, and notes.
- Interview stages currently support `Applied`, `HR Screen`, `Technical`, `Final`, `Offer`, and `Rejected`.
- Users can mark active interviews as `Rejected` or `Offer` from the interview expander.
- Users can append HR call notes to the interview `notes` field.
- The app lists active interviews where `stage` is not `Rejected` or `Offer`.
- The `Dashboard` page shows upcoming interviews with `next_step_date` in the next 7 days.
- Gmail integration fetches HR-related emails from Gmail via IMAP, stores matching messages in `email_logs`, deduplicates by Gmail message ID, and allows users to link each email to an interview via `email_logs.interview_id`.
- Richer HR contact management and closed-interview views remain planned.

### 4.5 Ideas

Ideas represent a backlog of possible projects, improvements, experiments, and career initiatives.

**Ideas table (`ideas`)**
- `id` (INTEGER, PK)
- `title` (TEXT, required)
- `category` (TEXT, optional)
- `status` (TEXT)
- `impact_estimate` (REAL, optional)
- `notes` (TEXT, optional)
- `created_at` (TEXT)

**Current and intended behavior**
- The `Ideas` page allows users to create, edit, and delete ideas.
- Ideas can be categorized with values such as `Career`, `Learning`, or `Automation Project`.
- Idea status should support values such as `Backlog`, `Next`, `In Progress`, `Done`, and `Dropped`.
- Users can filter ideas by category and status.
- Ideas are listed newest first based on `created_at`.

---

## 5. Pages and UX Requirements

### 5.1 Navigation

- Use a Streamlit sidebar control for these page names:
  - `Dashboard`
  - `Tasks`
  - `Skills`
  - `Time Tracking`
  - `Interviews`
  - `Ideas`
- Page names must stay consistent between `app.py`, README, and this spec.

### 5.2 Dashboard

The `Dashboard` page shows "today at a glance".

**Required dashboard sections**
- Today's Top 3 Tasks:
  - List tasks for today where `is_top3_for_day = 1` and `status != 'Done'`.
  - If fewer than three exist, show the available tasks.
- Task summary:
  - Show `X of Y tasks completed for today`, based on `due_date = today`.
- Upcoming Interviews:
  - Show interviews with `next_step_date` in the next 7 days.
- Skill Progress:
  - Show a pie chart or summary of total logged hours by skill from `skill_progress`.
- Time Summary:
  - Show today's `time_entries` aggregated by `category`, currently as a bar chart when data exists.

### 5.3 Tasks Page

The `Tasks` page is the main task-management surface.

**Required behavior**
- Provide a date selector, defaulting to today.
- On page load, call a model helper to ensure daily routine tasks exist for the selected date.
- Provide a task creation form for the selected date.
- Group task lists into:
  - Top 3 tasks for this date
  - Other tasks for this date
  - Completed tasks for this date
- Provide actions to mark done, toggle Top 3, edit, and delete.
- Keep task data access in `models.py`; do not write task SQL directly in `app.py`.

### 5.4 Skills Page

The `Skills` page is the skill-goal and learning-progress surface.

**Required behavior**
- Provide forms or controls to create, edit, and delete skills.
- Provide a form to log skill progress.
- Show all skills with total hours, target hours, and progress toward target.
- Show recent progress logs when useful.
- Provide data suitable for a chart of total hours by skill.
- Current UI supports create, edit, progress logging, total-hours metrics, progress bars, and dashboard chart data.
- Delete controls and richer progress-history views remain planned.
- Keep skill and progress data access in `models.py`.

### 5.5 Time Tracking Page

The `Time Tracking` page is the time-entry and category-summary surface.

**Required behavior**
- Provide a form to create time entries.
- Support start time, end time, category, notes, and optional linked task.
- Compute or validate `duration_minutes`.
- Show today's entries.
- Aggregate today's entries by `category`.
- Show category totals as a table and simple chart.
- Current UI supports start/end time, category, notes, duration validation, today's entries, category totals, and category charts.
- UI support for linking a time entry to a task remains planned.
- Keep time-entry data access in `models.py`.

### 5.6 Interviews Page

The `Interviews` page is the job-search pipeline and HR communication surface.

**Required behavior**
- Provide controls to create, edit, and delete HR contacts.
- Provide controls to create, edit, and delete interviews.
- Allow an interview to reference an HR contact with `hr_contact_id`.
- Show active interviews separately from closed interviews.
- Allow HR notes to be stored in the interview `notes` field for v1.
- Provide a Gmail import action for HR-related messages.
- Show recent `email_logs` with subject, sender, received time, snippet, and linked interview when available.
- Allow email logs to be linked to interviews.
- Current UI supports interview creation/editing, HR contact creation during interview creation, active interview listing, stage updates, HR call-note appending, Gmail fetch, email-log display, and email-to-interview linking.
- Standalone HR contact edit/delete controls and closed-interview views remain planned.
- Keep interview, contact, and email-log data access in `models.py`.

### 5.7 Ideas Page

The `Ideas` page is the project and initiative backlog surface.

**Required behavior**
- Provide a form to create ideas.
- Provide controls to edit and delete ideas.
- Support category, status, impact estimate, and notes.
- Filter ideas by category and status.
- List ideas newest first.
- Current UI supports idea creation, editing, deletion, filtering, impact estimates, notes, and backlog display.
- Keep idea data access in `models.py`.

---

## 6. Non-Functional Requirements

- Keep code simple, modular, and readable.
- Keep Streamlit UI functions small and page-specific.
- Keep database logic in `db.py` and `models.py`.
- Avoid inline SQL in `app.py`.
- Prefer standard library and small dependencies. Streamlit, pandas, matplotlib, and pytest are currently used.
- The app must run locally through `python -m streamlit run app.py`.
- The local SQLite database file `life_ops.db` must not be committed.
- Runtime artifacts such as `.venv/`, `__pycache__/`, `.pytest_cache/`, and `tests/.tmp/` must not be committed.
- Do not commit secrets, Gmail credentials, or `.streamlit/secrets.toml`.
- Gmail integration must read `GMAIL_USERNAME` and `GMAIL_APP_PASSWORD` from environment variables and must not store credentials in the database.
- README must stay aligned with the implemented state and include setup, run, database inspection, test, roadmap, and license notes.
- Tests should use isolated temporary SQLite databases rather than the real `life_ops.db`.

---

## 7. Testing Requirements

**Current testing**
- `tests/test_tasks.py` covers task behavior and daily routine behavior using isolated test databases.
- `tests/test_skills_and_time.py` covers skill progress summary totals and time summary totals by category using isolated test databases.
- `tests/test_interviews.py` covers active interview filtering, HR contact joins, note appending, upcoming interview windows, and email-log linking using isolated test databases.

**Required v1 testing**
- Task logic and daily routine cloning.
- Skill CRUD and progress totals.
- Time-entry duration and category aggregation.
- Interview, HR contact, and email-log linking behavior.
- Idea CRUD and filtering.
- Gmail parsing and deduplicated email-log storage.
- A small regression suite covering the core user flows.

---

## 8. Definition of Done for v1

- App runs via `python -m streamlit run app.py` with no runtime errors.
- `Dashboard`, `Tasks`, `Skills`, `Time Tracking`, `Interviews`, and `Ideas` pages are accessible.
- Tasks workflow is functional for daily planning and Top 3 tracking.
- Skills workflow is functional for goals, progress logging, and progress summaries.
- Time Tracking workflow is functional for logging entries and viewing category summaries.
- Interviews workflow is functional for tracking job opportunities, HR contacts, and notes.
- Gmail HR email import can store messages in `email_logs` and link them to interviews.
- Ideas workflow is functional for backlog entry, filtering, and status tracking.
- Tests pass on a fresh test database.
- The app is usable for daily operations without manual database edits.
