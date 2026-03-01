# TaskFlow — Task Management SaaS

Enterprise task management platform built with **Angular 21** and **Django 5.2 LTS**.

---

## Table of Contents

- [TaskFlow — Task Management SaaS](#taskflow--task-management-saas)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
    - [Recommended VS Code Extensions](#recommended-vs-code-extensions)
  - [Quick Start](#quick-start)
  - [Step-by-Step Setup](#step-by-step-setup)
    - [1. Backend — Python Environment](#1-backend--python-environment)
    - [2. PostgreSQL — Create Database](#2-postgresql--create-database)
    - [3. Migrations \& Superuser](#3-migrations--superuser)
    - [4. Frontend — Install Dependencies](#4-frontend--install-dependencies)
  - [Running the Application](#running-the-application)
    - [Option A — VS Code Launch Configs (Recommended)](#option-a--vs-code-launch-configs-recommended)
    - [Option B — Terminal Commands](#option-b--terminal-commands)
    - [Option C — Helper Scripts](#option-c--helper-scripts)
  - [Default Credentials](#default-credentials)
  - [Verifying It Works](#verifying-it-works)
  - [Known Limitations \& Future Features](#known-limitations--future-features)
    - [🔨 Missing Core Features](#-missing-core-features)
    - [📧 Email Integration (Not Implemented)](#-email-integration-not-implemented)
    - [🛠️ Additional Enhancements Needed](#️-additional-enhancements-needed)
  - [Project Structure](#project-structure)
  - [Technology Stack](#technology-stack)
    - [Backend](#backend)
    - [Frontend](#frontend)
    - [Infrastructure](#infrastructure)
  - [API Reference](#api-reference)
    - [Authentication](#authentication)
    - [Organizations](#organizations)
    - [Projects](#projects)
    - [Tasks](#tasks)
    - [Notifications](#notifications)
    - [Reports](#reports)
    - [Documentation](#documentation)
  - [Frontend Routes](#frontend-routes)
  - [Internationalization (i18n)](#internationalization-i18n)
    - [Task Workflow Values](#task-workflow-values)
    - [Email Integration (Future Feature)](#email-integration-future-feature)
  - [Docker (Full Stack)](#docker-full-stack)
  - [Troubleshooting](#troubleshooting)
    - [Backend won't start](#backend-wont-start)
    - [Application Limitations](#application-limitations)
    - [Frontend build fails](#frontend-build-fails)
    - [CORS errors in browser](#cors-errors-in-browser)
    - [Settings comparison](#settings-comparison)

---

## Prerequisites

| Tool       | Version   | Check Command        |
|------------|-----------|----------------------|
| Python     | 3.12+     | `python --version`   |
| Node.js    | 20.x LTS  | `node --version`     |
| npm        | 10.x+     | `npm --version`      |
| PostgreSQL | 16+       | `psql --version`     |
| Git        | 2.x+      | `git --version`      |

> **Python 3.14 Note:** Celery 5.6 hangs on import under Python 3.14. The `local` settings skip Celery entirely, so local development works fine.

### Recommended VS Code Extensions

| Extension                | ID                           |
|--------------------------|------------------------------|
| Python                   | `ms-python.python`           |
| Pylance                  | `ms-python.vscode-pylance`   |
| debugpy                  | `ms-python.debugpy`          |
| Angular Language Service | `angular.ng-template`        |
| ESLint                   | `dbaeumer.vscode-eslint`     |

---

## Quick Start

Run these four commands to go from zero to running:

```powershell
# 1 — Backend setup
cd d:\My\Saas\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements/dev.txt

# 2 — Create database & run migrations
.venv\Scripts\python.exe setup_pg.py
.venv\Scripts\python.exe setup_db.py

# 3 — Frontend setup
cd ..\frontend
npm install --legacy-peer-deps

# 4 — Open VS Code → Run & Debug → "Full Stack (Backend + Frontend)"
```

Then open **http://localhost:4200** and sign in with `admin@example.com` / `admin123456`.

---

## Step-by-Step Setup

### 1. Backend — Python Environment

```powershell
cd d:\My\Saas\backend
python -m venv .venv
.venv\Scripts\activate                     # Windows PowerShell
# source .venv/bin/activate               # macOS / Linux
pip install -r requirements/dev.txt
```

This installs Django 5.2, DRF, JWT auth, Celery, Channels, testing tools, linters, and type checkers.

### 2. PostgreSQL — Create Database

Make sure PostgreSQL is running at `127.0.0.1:5432`.

**Option A — Helper script** (connects via the `vector_db` database to create `taskmanager`):

```powershell
cd d:\My\Saas\backend
.venv\Scripts\python.exe setup_pg.py
```

**Option B — Manual SQL:**

```sql
CREATE DATABASE taskmanager;
```

**Connection details** used by `config/settings/local.py`:

| Setting  | Value         |
|----------|---------------|
| Host     | `127.0.0.1`   |
| Port     | `5432`        |
| Database | `taskmanager` |
| User     | `postgres`    |
| Password | `password`    |

Edit `backend/config/settings/local.py` to change these.

### 3. Migrations & Superuser

```powershell
cd d:\My\Saas\backend
.venv\Scripts\python.exe setup_db.py
```

This script does three things in order:
1. `makemigrations` — generates any missing migration files
2. `migrate` — creates all database tables
3. Creates a superuser `admin@example.com` / `admin123456` (skips if it already exists)

> **Note:** Migrations are centralized under `backend/scripts/migrations/` (configured via `MIGRATION_MODULES` in `base.py`), not inside each app's `migrations/` folder.

**Or run manually:**

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
.venv\Scripts\python.exe manage.py makemigrations
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py createsuperuser
```

### 4. Frontend — Install Dependencies

```powershell
cd d:\My\Saas\frontend
npm install --legacy-peer-deps
```

> `--legacy-peer-deps` is required because `@swimlane/ngx-charts` peer-depends on Angular 17/18, but the project uses Angular 21.

---

## Running the Application

### Option A — VS Code Launch Configs (Recommended)

Open **Run and Debug** (`Ctrl+Shift+D`) and select a configuration:

| Configuration                        | What It Does                                         |
|--------------------------------------|------------------------------------------------------|
| **Full Stack (Backend + Frontend)**  | Starts both servers in one click                     |
| **Full Stack + Chrome Debug**        | Both servers + opens Chrome with debugger attached   |
| **Backend: Django Server**           | Django on port 8000 with debugpy                     |
| **Backend: Setup DB**                | Runs migrations + creates superuser                  |
| **Backend: Create PG Database**      | Creates the `taskmanager` database in PostgreSQL     |
| **Backend: Django Shell**            | Interactive Django shell                             |
| **Backend: Run Tests**               | Runs pytest with verbose output                      |
| **Frontend: Angular Dev Server**     | Angular on port 4200 with API proxy                  |
| **Frontend: Open in Chrome**         | Attaches Chrome debugger to running frontend         |

**Recommended:** Select **"Full Stack (Backend + Frontend)"** and press `F5`.

### Option B — Terminal Commands

**Terminal 1 — Backend:**

```powershell
cd d:\My\Saas\backend
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

**Terminal 2 — Frontend:**

```powershell
cd d:\My\Saas\frontend
npx ng serve --proxy-config proxy.conf.json --port 4200
```

### Option C — Helper Scripts

```powershell
cd d:\My\Saas\backend
.venv\Scripts\python.exe run_server.py
```

This sets `DJANGO_SETTINGS_MODULE=config.settings.local` automatically and starts the backend on port 8000 with `--skip-checks --noreload`.

---

## Default Credentials

| Field    | Value              |
|----------|--------------------|
| Email    | `admin@example.com`|
| Password | `admin123456`      |

---

## Verifying It Works

Once both servers are running:

| Check                  | URL                                     |
|------------------------|-----------------------------------------|
| **Frontend app**       | http://localhost:4200                    |
| **Swagger API docs**   | http://localhost:8000/api/docs/          |
| **ReDoc API docs**     | http://localhost:8000/api/redoc/         |
| **Django Admin**       | http://localhost:8000/admin/             |

1. Open http://localhost:4200 — you should see the login page.
2. Sign in with `admin@example.com` / `admin123456`.
3. You'll land on the **Dashboard**. Current available features:
   - ✅ Create and manage organizations
   - ✅ Create and manage projects  
   - ✅ View tasks on a Kanban board
   - ✅ Assign tasks, set priorities and due dates
   - ✅ View reports and analytics
   - ✅ Manage users and teams under **Admin → Settings**
   - ✅ Multi-language support (English, Spanish, French)
   - ✅ Task status and priority badges with color coding

## Known Limitations & Future Features

The following features are documented but **not yet implemented**:

### 🔨 Missing Core Features
- **Task Creation UI**: No "Create Task" button in My Tasks page
- **Enhanced Profile Management**: Cannot edit profile settings from UI
- **Theme Switching**: No dark/light mode toggle
- **Language Selector**: No UI to switch between en/es/fr
- **Task Assignment**: Limited task creation and assignment workflows

### 📧 Email Integration (Not Implemented)
- **IMAP Configuration**: Incoming email processing
- **SMTP Configuration**: Outgoing email notifications  
- **Email-to-Task**: Create tasks by sending emails
- **Email Notifications**: Task updates and assignments via email

### 🛠️ Additional Enhancements Needed
- **User Preferences**: Theme, language, notification settings
- **Advanced Task Filters**: Better search and filtering
- **File Upload**: Task attachments and documents
- **Time Tracking**: Built-in timer and time logging
- **Advanced Reporting**: Custom date ranges, exports
- **Mobile Responsive**: Improved mobile/tablet experience

---

## Project Structure

```
d:\My\Saas\
├── .vscode/
│   └── launch.json                    # VS Code debug/run configurations
│
├── backend/                           # Django 5.2 LTS backend
│   ├── .venv/                         # Python virtual environment
│   ├── apps/
│   │   ├── users/                     # User auth, registration, profile, user management
│   │   ├── organizations/             # Orgs, org members, teams, team members
│   │   ├── projects/                  # Projects, boards, columns, project members
│   │   ├── tasks/                     # Tasks, comments, attachments, activity logs
│   │   ├── notifications/             # In-app notifications
│   │   ├── reports/                   # Analytics, burndown, velocity, workload
│   │   └── common/                    # Shared base models (TimeStampedModel, etc.)
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py                # Shared settings (MIGRATION_MODULES, INSTALLED_APPS)
│   │   │   ├── local.py               # ★ Local dev — PostgreSQL, no Redis/Celery/Daphne
│   │   │   ├── development.py         # Full dev stack — requires Redis
│   │   │   ├── production.py          # Production settings
│   │   │   └── test.py                # Test runner settings
│   │   ├── urls.py                    # URL routing (api/v1/...)
│   │   └── celery.py                  # Celery configuration
│   ├── scripts/
│   │   └── migrations/                # ★ Centralized Django migrations
│   │       ├── users/                 #   (3 migration files)
│   │       ├── organizations/         #   (5 migration files)
│   │       ├── projects/              #   (4 migration files)
│   │       ├── tasks/                 #   (4 migration files)
│   │       ├── notifications/         #   (2 migration files)
│   │       └── reports/               #   (empty — no models)
│   ├── requirements/
│   │   ├── base.txt                   # Core: Django, DRF, JWT, Celery, Channels
│   │   ├── dev.txt                    # Dev: pytest, ruff, mypy, debug-toolbar
│   │   └── prod.txt                   # Production: gunicorn, sentry, etc.
│   ├── tests/                         # pytest test suite
│   ├── manage.py                      # Django management CLI
│   ├── run_server.py                  # Quick-start dev server helper
│   ├── setup_db.py                    # Auto-migrate + create superuser
│   └── setup_pg.py                    # Create PostgreSQL database
│
├── frontend/                          # Angular 21 frontend
│   ├── src/app/
│   │   ├── core/
│   │   │   ├── i18n/                  # Translations: en.ts, es.ts, fr.ts
│   │   │   ├── models/               # TypeScript interfaces (User, Task, Project, etc.)
│   │   │   ├── services/             # API services (auth, task, project, org, team, etc.)
│   │   │   ├── guards/               # Route guards (auth, guest)
│   │   │   └── interceptors/         # HTTP interceptors (JWT, error handling)
│   │   ├── features/
│   │   │   ├── auth/                  # Login, Register, Forgot Password
│   │   │   ├── dashboard/             # Dashboard with stats and recent projects
│   │   │   ├── projects/              # Project list, detail, create/edit form
│   │   │   ├── board/                 # Kanban board with drag-and-drop
│   │   │   ├── task-list/             # Task list with filters (status, priority)
│   │   │   ├── task-detail/           # Task detail with assignee, comments, attachments
│   │   │   ├── reports/               # Charts: burndown, velocity, workload
│   │   │   ├── notifications/         # Notification list with mark-read
│   │   │   ├── profile/               # User profile, change password, preferences
│   │   │   └── admin/                 # Organization settings + sub-pages:
│   │   │       ├── org-settings/      #   Create/edit organization
│   │   │       ├── member-management/ #   Invite/remove org members, change roles
│   │   │       ├── user-management/   #   Admin CRUD for users
│   │   │       └── team-management/   #   Create teams, add/remove team members
│   │   ├── layout/
│   │   │   ├── shell/                 # Main app shell (sidebar + content)
│   │   │   ├── header/                # Top navigation bar
│   │   │   └── sidebar/               # Side navigation
│   │   └── shared/
│   │       ├── components/            # Reusable: status-badge, priority-badge,
│   │       │                          #   user-avatar, loading-spinner, toast, etc.
│   │       ├── pipes/                 # translate, timeAgo
│   │       └── services/              # toast, confirm-dialog
│   ├── proxy.conf.json                # Proxies /api/* → localhost:8000
│   ├── angular.json                   # Angular CLI configuration
│   └── package.json                   # Dependencies (Angular 21, Bootstrap 5, ngx-charts)
│
├── features/                          # 10 Gherkin BDD specifications
│   ├── 01_user_authentication.feature
│   ├── 02_organization_management.feature
│   ├── 03_project_management.feature
│   ├── 04_task_management.feature
│   ├── 05_kanban_board.feature
│   ├── 06_notifications.feature
│   ├── 07_reports_analytics.feature
│   ├── 08_admin_panel.feature
│   ├── 09_layout_navigation_shared.feature
│   └── 10_infrastructure_deployment.feature
│
├── docker-compose.yml                 # Full stack Docker (PostgreSQL, Redis, Celery)
├── docker-compose.prod.yml            # Production Docker config
├── nginx/nginx.conf                   # Nginx reverse proxy configuration
├── README.md                          # Project overview
└── readme-functionality.md            # Detailed feature specifications
```

---

## Technology Stack

### Backend

| Component        | Technology                              |
|------------------|-----------------------------------------|
| Framework        | Django 5.2 LTS                          |
| API              | Django REST Framework 3.16              |
| Auth             | Simple JWT 5.5 (access + refresh tokens)|
| Database         | PostgreSQL 16+                          |
| Caching          | Django Redis 5.4 (local: in-memory)     |
| WebSockets       | Django Channels 4.3                     |
| Task Queue       | Celery 5.6 (local: eager/synchronous)   |
| API Docs         | drf-spectacular (Swagger + ReDoc)       |
| Testing          | pytest, factory-boy, faker              |
| Linting          | ruff, black, isort, mypy                |

### Frontend

| Component        | Technology                    |
|------------------|-------------------------------|
| Framework        | Angular 21                    |
| Language         | TypeScript 5.9                |
| CSS Framework    | Bootstrap 5.3                 |
| Charts           | @swimlane/ngx-charts          |
| Icons            | Bootstrap Icons               |
| i18n             | Custom TranslationService     |
| State Management | Angular Signals               |

### Infrastructure

| Component        | Technology                    |
|------------------|-------------------------------|
| Containers       | Docker, Docker Compose        |
| Reverse Proxy    | Nginx                         |
| CI/CD            | GitHub Actions                |

---

## API Reference

### Authentication

| Method | Endpoint                       | Description                   |
|--------|--------------------------------|-------------------------------|
| POST   | `/api/v1/auth/token/`          | Login → JWT access + refresh  |
| POST   | `/api/v1/auth/token/refresh/`  | Refresh access token          |
| POST   | `/api/v1/auth/register/`       | Register new user             |
| GET    | `/api/v1/auth/me/`             | Get current user profile      |
| PATCH  | `/api/v1/auth/me/`             | Update profile                |
| POST   | `/api/v1/auth/change-password/`| Change password               |

### Organizations

| Method | Endpoint                                        | Description              |
|--------|-------------------------------------------------|--------------------------|
| GET    | `/api/v1/organizations/`                        | List organizations       |
| POST   | `/api/v1/organizations/`                        | Create organization      |
| GET    | `/api/v1/organizations/{id}/`                   | Get organization detail  |
| PATCH  | `/api/v1/organizations/{id}/`                   | Update organization      |
| GET    | `/api/v1/organizations/{id}/members/`           | List org members         |
| POST   | `/api/v1/organizations/{id}/members/add/`       | Invite member            |
| PATCH  | `/api/v1/organizations/{id}/members/{mid}/role/`| Change member role       |
| DELETE | `/api/v1/organizations/{id}/members/{mid}/`     | Remove member            |

### Projects

| Method | Endpoint                              | Description              |
|--------|---------------------------------------|--------------------------|
| GET    | `/api/v1/projects/`                   | List projects            |
| POST   | `/api/v1/projects/`                   | Create project           |
| GET    | `/api/v1/projects/{id}/`              | Get project detail       |
| PATCH  | `/api/v1/projects/{id}/`              | Update project           |
| DELETE | `/api/v1/projects/{id}/`              | Delete project           |
| POST   | `/api/v1/projects/{id}/archive/`      | Archive project          |
| POST   | `/api/v1/projects/{id}/restore/`      | Restore archived project |
| GET    | `/api/v1/projects/{id}/members/`      | List project members     |
| POST   | `/api/v1/projects/{id}/members/add/`  | Add project member       |
| GET    | `/api/v1/projects/boards/`            | List boards              |
| POST   | `/api/v1/projects/columns/`           | Create column            |
| POST   | `/api/v1/projects/columns/reorder/`   | Reorder columns          |

### Tasks

| Method | Endpoint                                | Description              |
|--------|-----------------------------------------|--------------------------|
| GET    | `/api/v1/tasks/`                        | List tasks (filterable)  |
| POST   | `/api/v1/tasks/`                        | Create task              |
| GET    | `/api/v1/tasks/{id}/`                   | Get task detail          |
| PATCH  | `/api/v1/tasks/{id}/`                   | Update task              |
| DELETE | `/api/v1/tasks/{id}/`                   | Delete task              |
| POST   | `/api/v1/tasks/{id}/move/`              | Move task (column/position) |
| GET    | `/api/v1/tasks/{id}/comments/`          | List comments            |
| POST   | `/api/v1/tasks/{id}/comments/`          | Add comment              |
| GET    | `/api/v1/tasks/{id}/attachments/`       | List attachments         |
| POST   | `/api/v1/tasks/{id}/attachments/`       | Upload attachment        |
| GET    | `/api/v1/tasks/{id}/activity/`          | Activity log             |

### Notifications

| Method | Endpoint                                  | Description              |
|--------|-------------------------------------------|--------------------------|
| GET    | `/api/v1/notifications/`                  | List notifications       |
| POST   | `/api/v1/notifications/mark-all-read/`    | Mark all as read         |
| POST   | `/api/v1/notifications/clear-read/`       | Clear read notifications |

### Reports

| Method | Endpoint                                                | Description              |
|--------|---------------------------------------------------------|--------------------------|
| GET    | `/api/v1/projects/{project_id}/reports/summary/`        | Project summary          |
| GET    | `/api/v1/projects/{project_id}/reports/status/`         | Status distribution      |
| GET    | `/api/v1/projects/{project_id}/reports/priority/`       | Priority distribution    |
| GET    | `/api/v1/projects/{project_id}/reports/burndown/`       | Burndown chart data      |
| GET    | `/api/v1/projects/{project_id}/reports/velocity/`       | Velocity chart data      |
| GET    | `/api/v1/projects/{project_id}/reports/workload/`       | Assignee workload        |
| GET    | `/api/v1/projects/{project_id}/reports/export/csv/`     | Export CSV               |

### Documentation

| URL                            | Description    |
|--------------------------------|----------------|
| `http://localhost:8000/api/docs/`  | Swagger UI |
| `http://localhost:8000/api/redoc/` | ReDoc      |

---

## Frontend Routes

| Path                        | Component                | Auth Required |
|-----------------------------|--------------------------|:---:|
| `/auth/login`               | Login                    | No  |
| `/auth/register`            | Register                 | No  |
| `/auth/forgot-password`     | Forgot Password          | No  |
| `/dashboard`                | Dashboard                | Yes |
| `/projects`                 | Project List             | Yes |
| `/projects/:id`             | Project Detail           | Yes |
| `/projects/new`             | Create Project           | Yes |
| `/projects/:id/edit`        | Edit Project             | Yes |
| `/board/:boardId`           | Kanban Board             | Yes |
| `/tasks`                    | My Tasks (assigned to me)| Yes |
| `/tasks/:taskId`            | Task Detail              | Yes |
| `/reports/:projectId`       | Project Reports          | Yes |
| `/notifications`            | Notification List        | Yes |
| `/profile`                  | User Profile & Preferences | Yes |
| `/tasks/new`                | Create New Task          | Yes |
| `/admin`                    | Organization Settings    | Yes |
| `/admin/members`            | Member Management        | Yes |
| `/admin/users`              | User Management          | Yes |
| `/admin/teams`              | Team Management          | Yes |

---

## Internationalization (i18n)

The app supports three languages via `frontend/src/app/core/i18n/`:

| File    | Language |
|---------|----------|
| `en.ts` | English (default) |
| `es.ts` | Spanish  |
| `fr.ts` | French   |

All UI labels, status names, priority names, form labels, and toast messages use the `TranslatePipe` (`{{ 'key' | translate }}`) backed by a `TranslationService`.

### Task Workflow Values

**Statuses:** `backlog` → `todo` → `in_progress` → `in_review` → `done` | `cancelled`

**Priorities:** `low` | `medium` | `high` | `critical`

**User Roles:** `admin` | `manager` | `member`

**Organization Roles:** `owner` | `admin` | `member`

**Project Member Roles:** `admin` | `member` | `viewer`

### Email Integration (Future Feature)

When implemented, the system will support:

**IMAP Configuration:**
- Incoming email server settings
- Email-to-task parsing rules
- Automatic task creation from emails
- Attachment handling

**SMTP Configuration:**  
- Outgoing email server settings
- Task assignment notifications
- Status change alerts
- Daily/weekly digest emails

**Email-to-Task Workflow:**
1. Send email to `tasks@yourcompany.com`
2. Subject becomes task title
3. Body becomes task description  
4. Attachments are preserved
5. Sender becomes task reporter
6. Email routing rules assign to projects/users

---

## Docker (Full Stack)

For running the full stack with Docker Compose (PostgreSQL, Redis, Celery worker, Django, Nginx):

```bash
docker-compose up --build
```

This uses `config/settings/development.py` which requires Redis for caching and Celery for async tasks.

For production:

```bash
docker-compose -f docker-compose.prod.yml up --build
```

---

## Troubleshooting

### Backend won't start

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'storages'` | You're using `development.py` settings. Switch to `local.py`: set `$env:DJANGO_SETTINGS_MODULE = "config.settings.local"` |
| `ModuleNotFoundError: No module named 'django_redis'` | Same as above — `local.py` uses in-memory cache, no Redis needed |
| Celery import hangs (Python 3.14) | `local.py` settings skip Celery automatically |
| Port 8000 in use | `netstat -ano \| findstr :8000` then `Stop-Process -Id <PID> -Force` |
| Database connection refused | Ensure PostgreSQL is running on port 5432 |
| Password authentication failed for user "taskmanager" | You're using `development.py` (expects user `taskmanager`). Use `local.py` (connects as `postgres`) |

### Application Limitations

| Issue | Current Status |
|-------|----------------|
| No "Create Task" button in UI | **Missing Feature** — Task creation UI not implemented |
| Cannot edit profile | **Missing Feature** — Profile edit form needs enhancement |
| No language switcher | **Missing Feature** — i18n files exist but no UI selector |
| No theme toggle | **Missing Feature** — Dark/light mode not implemented |
| No email integration | **Missing Feature** — IMAP/SMTP configuration needed |
| Tasks not created via email | **Missing Feature** — Email parsing service not built |

### Frontend build fails

| Problem | Solution |
|---------|----------|
| TypeScript version mismatch | Angular 21 requires TS ≥5.9: `npm install typescript@~5.9.0 --legacy-peer-deps` |
| Peer dependency conflicts | Always use `npm install --legacy-peer-deps` |
| Port 4200 in use | `npx ng serve --port 4201` |

### CORS errors in browser

The Angular dev server uses `proxy.conf.json` to forward `/api/*` and `/ws/*` to `localhost:8000`, avoiding CORS entirely. If you access the backend directly, `local.py` allows origins `http://localhost:4200` and `http://127.0.0.1:4200`.

### Settings comparison

| Feature            | `local.py` (recommended)         | `development.py`                 |
|--------------------|----------------------------------|----------------------------------|
| Database user      | `postgres`                       | `taskmanager`                    |
| Cache              | In-memory (no Redis)             | Redis required                   |
| Celery             | Eager mode (synchronous)         | Requires broker (Redis/RabbitMQ) |
| WebSocket layer    | In-memory                        | Redis required                   |
| ASGI server        | Django dev server                | Daphne                           |
| Extra apps         | `django_extensions` (optional)   | `django_extensions` (required)   |
