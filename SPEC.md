# Life Ops Console – SPEC

## 1. Overview

**Name:** Life Ops Console  
**Purpose:** A single, personal “operations console” to manage my job search, skills, tasks, and time. It replaces scattered spreadsheets, notes, and calendars with a focused dashboard.

**User:** Single user (me). No authentication or multi-tenant support required.

**High-level goals:**
- Track and plan daily work with a clear “Top 3 tasks for today”.
- Track skill-building and show visual progress (bars + pie chart).
- Track interviews and HR interactions, including Gmail-based HR emails.
- Log time spent in learning, planning, job search, and admin work.
- Maintain a backlog of ideas for future projects or initiatives.

The app is for **personal use** but should be built with clean structure and tests so it can be used as a **portfolio-quality project**.

---

## 2. Tech Stack and Architecture

**Runtime & language**
- Python 3.x

**Frontend / UI**
- Streamlit (single-page app with sidebar-based navigation)

**Database**
- SQLite (single file, e.g. `life_ops.db`)

**App architecture**
- Simple monolith, no microservices.
- Streamlit app (`app.py`) imports DB helpers (`db.py` / `models.py`) for all data access.
- No user authentication; assume trusted single user environment.

**Key modules/files (initial target)**
- `SPEC.md` – this file, source of truth for requirements.
- `app.py` – Streamlit entry point, navigation, and page composition.
- `db.py` – SQLite connection and `init_db()` to create tables.
- `models.py` – CRUD helpers and query functions for each table.
- `gmail_integration.py` – Gmail-only integration for fetching HR emails (read-only).
- `tests/` – pytest-based test suite:
  - `tests/test_tasks.py`
  - `tests/test_skills_and_time.py`
  - `tests/test_regression.py`

---

## 3. Core Domains and Data Model

### 3.1 Tasks

Represents actionable items tied to specific dates.

**Tasks table (`tasks`)**
- `id` (INTEGER, PK)
- `title` (TEXT, required)
- `description` (TEXT, optional)
- `due_date` (TEXT or DATE, required) – date this task is planned for
- `priority` (TEXT) – one of: `Low`, `Medium`, `High`
- `status` (TEXT) – one of: `Pending`, `In Progress`, `Done`
- `is_top3_for_day` (INTEGER 0/1) – whether it is one of the “top 3” tasks for that date
- `is_daily_routine` (INTEGER 0/1) – whether this is a reusable “routine template”
- `created_at` (TEXT or DATETIME)

**Behaviors:**
- There is a concept of a “selected date” on the Tasks page (default: today).
- “Daily routine” tasks are templates: when I open the Tasks page for a date, the app ensures routine tasks exist for that date by cloning templates if needed.
- “Top 3” tasks are visually highlighted and surfaced on both Tasks page and Dashboard.

### 3.2 Skills & Skill Progress

Represents learning goals and logged progress.

**Skills table (`skills`)**
- `id` (INTEGER, PK)
- `name` (TEXT, required) – e.g. “Python”, “Appium”, “AI QA”
- `category` (TEXT, optional) – e.g. “Language”, “Automation”, “AI”
- `target_hours` (REAL, required) – target learning hours
- `created_at` (TEXT or DATETIME)

**Skill progress table (`skill_progress`)**
- `id` (INTEGER, PK)
- `skill_id` (INTEGER, FK → `skills.id`)
- `date` (TEXT or DATE)
- `hours_spent` (REAL)
- `notes` (TEXT, optional)

**Behaviors:**
- I can create/edit skills and set target hours.
- I can log learning sessions against skills.
- The app shows:
  - Per-skill progress bars (total hours vs target).
  - A summary and a pie chart of total hours per skill.

### 3.3 Time Tracking

Represents blocks of time spent in different categories.

**Time entries table (`time_entries`)**
- `id` (INTEGER, PK)
- `start_time` (TEXT or DATETIME)
- `end_time` (TEXT or DATETIME)
- `duration_minutes` (INTEGER or REAL)
- `category` (TEXT) – e.g. `Learning`, `Planning`, `Job Search`, `Admin`
- `notes` (TEXT, optional)
- `task_id` (INTEGER, optional FK → `tasks.id`)

**Behaviors:**
- I can log time entries by picking start time, end time, category, notes.
- The app computes duration.
- The app shows:
  - Today’s entries and totals per category.
  - A simple bar/pie chart for “time by category” (today or recent days).

### 3.4 Interviews / HR Calls / Email Logs

Tracks interviews and associated communication.

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
- `stage` (TEXT) – e.g. `Applied`, `Screening`, `Round 1`, `Round 2`, `HR Round`, `Offer`, `Rejected`, `Closed`
- `next_step_date` (TEXT or DATE, optional) – next important date for this interview
- `hr_contact_id` (INTEGER, FK → `hr_contacts.id`, optional)
- `notes` (TEXT, optional)
- `created_at` (TEXT or DATETIME)

**HR call logs (can be a simple child table or just notes field)**
- For v1, storing detailed call logs in `notes` is acceptable.

**Email logs table (`email_logs`)**
- `id` (INTEGER, PK)
- `provider` (TEXT) – for v1 always `'Gmail'`
- `message_id` (TEXT)
- `subject` (TEXT)
- `sender` (TEXT)
- `received_at` (TEXT or DATETIME)
- `snippet` (TEXT)
- `interview_id` (INTEGER, FK → `interviews.id`, nullable)

**Behaviors:**
- I can create/edit interviews and mark them as closed (e.g. `Rejected`, `Offer accepted`).
- I can see upcoming interviews (e.g. next 7 days) on the Dashboard.
- I can fetch recent HR‑related Gmail emails and store them as `email_logs`.
- I can manually link stored emails to an interview (`email_logs.interview_id`).

### 3.5 Ideas

Represents backlog of ideas for projects, improvements, experiments.

**Ideas table (`ideas`)**
- `id` (INTEGER, PK)
- `title` (TEXT, required)
- `category` (TEXT, optional) – e.g. `Career`, `Learning`, `Automation Project`
- `status` (TEXT) – e.g. `Backlog`, `Next`, `In Progress`, `Done`, `Dropped`
- `impact_estimate` (REAL, optional) – rough 1–10 or similar
- `notes` (TEXT, optional)
- `created_at` (TEXT or DATETIME)

**Behaviors:**
- I can add/edit ideas.
- I can filter by category and status.
- Ideas are shown sorted by `created_at` (newest first).

---

## 4. Pages and UX Requirements

### 4.1 Navigation

- Use a Streamlit sidebar with radio buttons or selectbox for:
  - Dashboard
  - Tasks
  - Skills
  - Time Tracking
  - Interviews
  - Ideas

### 4.2 Dashboard

Dashboard shows “today at a glance”:

- **Today’s Top 3 Tasks**
  - List tasks for today where `is_top3_for_day = 1` and `status != 'Done'`.
  - If fewer than 3 exist, just show what is available.
- **Task summary**
  - “X of Y tasks completed for today” (based on `due_date = today`).
- **Upcoming Interviews**
  - Interviews with `next_step_date` in the next 7 days.
- **Skill Progress Pie Chart**
  - Pie chart of `total_hours` per skill based on `skill_progress`.
- **Time Summary**
  - Bar or pie chart of today’s `time_entries` aggregated by `category`.

### 4.3 Tasks Page

- Date selector at top (default: today).
- On load:
  - Call a helper to ensure that daily routine tasks are instantiated for the selected date.
- Sections:
  - “Top 3 tasks for this date” – tasks with `due_date = selected_date`, `is_top3_for_day = 1`, `status != 'Done'`.
  - “Other tasks for this date” – tasks with `due_date = selected_date`, `status != 'Done'`, not in top 3.
  - “Completed tasks for this date” – tasks with `due_date = selected_date`, `status = 'Done'`.
- Forms / actions:
  - Create task for selected date (title, description, priority, status, checkboxes for `is_top3_for_day`, `is_daily_routine`).
  - Mark task as Done.
  - Toggle `is_top3_for_day`.
  - Edit or delete tasks.
- For v1, just use a list/table layout grouped by the sections above (no calendar widget).

### 4.4 Skills Page

- Section to manage skills:
  - Form to create/edit skills (name, category, target_hours).
  - Table of all skills with total hours, target hours, and a progress bar.
- Section to log skill progress:
  - Form with dropdown to select skill, date, hours_spent, notes.
  - List of recent logs (optional).
- The page should reuse helpers that:
  - Calculate `total_hours` per skill.
  - Provide data structures that are easy to feed into charts.

### 4.5 Time Tracking Page

- Form to log time entries:
  - Start time, end time, category, notes (optional), optional task link.
  - App computes `duration_minutes`.
- List/table of today’s entries.
- Summary:
  - Aggregate today’s time by category and show as table + simple chart.

### 4.6 Interviews Page

- Section to create/edit interviews:
  - Fields: company, role, stage, next_step_date, HR contact (selected or new), notes.
- Section to list active interviews (not closed):
  - Show company, role, stage, next_step_date, HR contact.
  - Provide a way to mark interview as closed (status like `Rejected`, `Offer`, etc.).
- Section for HR call notes:
  - For v1, this can be a text area appended to the interview notes.
- Section for Gmail emails:
  - Button: “Fetch latest HR emails from Gmail”.
  - Table of recent `email_logs` (subject, sender, received_at, snippet).
  - Per‑row dropdown to select an interview and a button to link the email to that interview.

### 4.7 Ideas Page

- Form to add a new idea: title, category, status, impact_estimate, notes.
- Filters for category and status.
- Table/list of ideas sorted by newest first.

---

## 5. Non‑Functional Requirements

- Keep code simple, modular, and readable.
- No heavy frameworks beyond Streamlit and standard Python libraries plus small utilities (e.g., `pandas` if needed).
- Database interactions go through helper functions in `models.py` rather than raw SQL scattered in UI.
- Provide a `README.md` with:
  - Setup instructions.
  - How to run the app.
  - How to configure Gmail integration.
- Provide basic tests using pytest for:
  - Task logic and daily routines.
  - Skill and time tracking summaries.
  - A small end‑to‑end regression covering core flows.

---

## 6. Definition of Done for v1

- App runs via `python -m streamlit run app.py` with no runtime errors.
- All pages (Dashboard, Tasks, Skills, Time Tracking, Interviews, Ideas) are accessible and functional.
- Gmail integration for HR emails:
  - If configured correctly, recent emails are fetched and stored in `email_logs`.
  - Emails can be linked to interviews.
- Tests in `tests/` pass on a fresh test database.
- The app is usable for daily operations (tasks, interviews, skills, time logging) without manual DB edits.
