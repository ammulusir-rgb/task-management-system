# Task Manager SaaS — Complete Functionality Guide

> A step-by-step explanation of every feature in the enterprise Task Management platform.

---

## Table of Contents

1. [User Authentication & Account Management](#1-user-authentication--account-management)
2. [Organization Management (Multi-Tenancy)](#2-organization-management-multi-tenancy)
3. [Project Management](#3-project-management)
4. [Task Management (Core Domain)](#4-task-management-core-domain)
5. [Kanban Board (Drag & Drop)](#5-kanban-board-drag--drop)
6. [Notifications System](#6-notifications-system)
7. [Reports & Analytics Dashboard](#7-reports--analytics-dashboard)
8. [Admin Panel](#8-admin-panel)
9. [Layout, Navigation & Shared Components](#9-layout-navigation--shared-components)
10. [Infrastructure, Deployment & Security](#10-infrastructure-deployment--security)

---

## 1. User Authentication & Account Management

**Module:** `apps/users` | **JWT Strategy:** Access token in memory, Refresh token in HttpOnly cookie

### 1.1 User Registration

| Step | What Happens |
|------|-------------|
| 1 | User submits **email, first name, last name, password, password confirmation** via `POST /api/v1/auth/register/` |
| 2 | Backend validates: unique email, password strength (Django validators), passwords match |
| 3 | A new `User` record is created with UUID primary key, email as username, and default role `MEMBER` |
| 4 | Backend returns a short-lived **access JWT** in the response body |
| 5 | Backend sets a **refresh token** in an `HttpOnly` / `Secure` / `SameSite=Lax` cookie (7-day lifetime, path restricted to `/api/v1/auth/token/`) |
| 6 | A **Celery background task** dispatches a welcome email to the new user |

**Validation rules:**
- Duplicate email → `400 Bad Request`
- Weak password (e.g., "123") → `400 Bad Request` with complexity error
- Mismatched passwords → `400 Bad Request` with "Passwords do not match"

### 1.2 Login (JWT Token Obtain)

| Step | What Happens |
|------|-------------|
| 1 | User submits **email + password** to `POST /api/v1/auth/token/` |
| 2 | Backend authenticates credentials and generates JWT pair |
| 3 | The **access token** (15-min lifetime) is returned in the JSON body with custom claims: `email`, `role`, `full_name` |
| 4 | The **refresh token** is set as an HttpOnly cookie — it is **never** exposed in the response body |
| 5 | Rate limiting: after **5 failed attempts** in 1 minute, the endpoint returns `429 Too Many Requests` with a `Retry-After` header |

### 1.3 Silent Token Refresh

| Step | What Happens |
|------|-------------|
| 1 | The Angular frontend `AuthService` schedules a silent refresh timer that fires **every 4 minutes** |
| 2 | A `POST /api/v1/auth/token/refresh/` request is sent — the browser automatically includes the HttpOnly refresh cookie |
| 3 | Backend **rotates** the refresh token (blacklists the old one) and returns a new access token |
| 4 | A new refresh cookie is set simultaneously |
| 5 | The access token is stored in an **Angular signal** (memory only) — never in `localStorage` or `sessionStorage` |
| 6 | If the refresh cookie is expired (>7 days), the response is `401 Unauthorized` and the user is redirected to login |

### 1.4 Logout

| Step | What Happens |
|------|-------------|
| 1 | User clicks "Sign Out" or calls `POST /api/v1/auth/logout/` |
| 2 | Backend **blacklists** the refresh token in the database |
| 3 | The `refresh_token` cookie is **cleared** |
| 4 | Angular `AuthService` clears the access token signal, clears the current user signal, cancels the refresh timer, and navigates to `/auth/login` |

### 1.5 User Profile

- **View:** `GET /api/v1/users/me/` returns `id`, `email`, `first_name`, `last_name`, `role`, `avatar`, `phone`, `job_title`
- **Update:** `PATCH /api/v1/users/me/` to change name, job title, phone, etc.
- **Change Password:** `POST /api/v1/users/change-password/` with `current_password`, `new_password`, `new_password_confirm`

---

## 2. Organization Management (Multi-Tenancy)

**Module:** `apps/organizations` | **Roles hierarchy:** OWNER > ADMIN > MEMBER

### 2.1 Organization CRUD

| Step | What Happens |
|------|-------------|
| 1 | Authenticated user sends `POST /api/v1/organizations/` with `name`, `description`, `website` |
| 2 | A **slug** is auto-generated from the name (e.g., "Acme Corporation" → `acme-corporation`). If a slug already exists, a numeric suffix is appended (`acme-corporation-1`) |
| 3 | The creating user automatically becomes the **OWNER** via an `OrganizationMember` record |
| 4 | `GET /api/v1/organizations/` lists all orgs where the user is a member, each with its `member_count` |
| 5 | `GET /api/v1/organizations/{id}/` returns full org details including `id`, `name`, `slug`, `description`, `logo`, `member_count`, `created_at` |
| 6 | `PATCH /api/v1/organizations/{id}/` allows OWNER/ADMIN to update name, description |
| 7 | **MEMBER** role cannot update org settings → `403 Forbidden` |

### 2.2 Member Management

| Action | Endpoint | Who Can Do It | What Happens |
|--------|----------|---------------|-------------|
| **List members** | `GET /organizations/{id}/members/` | Any member | Returns all members with `user`, `role`, `joined_at` |
| **Invite member** | `POST /organizations/{id}/members/` | OWNER or ADMIN | Adds user by email with chosen role; sends notification |
| **Change role** | `PATCH /organizations/{id}/members/{mid}/` | OWNER only | Updates role; MEMBER cannot change roles (403) |
| **Remove member** | `DELETE /organizations/{id}/members/{mid}/` | OWNER only | Removes member and revokes access to all org projects |
| **Protection** | — | — | The **last OWNER** cannot be removed → `400 Bad Request` |

### 2.3 Permissions

- Non-members cannot access any organization data → `403 Forbidden`
- Each organization is a fully isolated **tenant**

---

## 3. Project Management

**Module:** `apps/projects` | **Includes:** Projects, Boards, Columns, Project Members

### 3.1 Project CRUD

| Step | What Happens |
|------|-------------|
| 1 | User sends `POST /api/v1/projects/` with `organization`, `name`, `description`, `prefix`, `start_date`, `end_date` |
| 2 | A **slug** is auto-generated (unique within the org). The **prefix** is auto-generated from the first letter of each word if not provided (e.g., "Mobile App Development" → `MAD`) |
| 3 | A **default Kanban board** named "Main Board" is automatically created via a `post_save` signal |
| 4 | The default board gets **5 columns**: Backlog (gray), To Do (blue), In Progress (yellow), In Review (cyan), Done (green, marked as `is_done_column`) |
| 5 | The creating user is auto-added as **project ADMIN** |

**Project statuses:** `ACTIVE` | `ARCHIVED`

### 3.2 Project Listing & Details

- `GET /api/v1/projects/` lists projects the user can access with `task_count`, `member_count`, `status`, `prefix`, `created_at`
- `GET /api/v1/projects/{id}/` returns full project details including all boards and their columns

### 3.3 Archive / Restore (Soft Delete)

| Action | Endpoint | What Happens |
|--------|----------|-------------|
| **Archive** | `POST /projects/{id}/archive/` | Sets `deleted_at` timestamp, status becomes `ARCHIVED`, project becomes read-only |
| **Restore** | `POST /projects/{id}/restore/` | Clears `deleted_at`, status returns to `ACTIVE` |

### 3.4 Project Members

| Role | Capabilities |
|------|-------------|
| **ADMIN** | Full project control, manage members, edit settings |
| **MEMBER** | Create/edit tasks, move cards, add comments |
| **VIEWER** | Read-only access (cannot create or modify tasks → `403`) |

### 3.5 Boards & Columns

- **Create additional boards:** `POST /projects/{id}/boards/` with a `name`
- **Add column:** Specify `name`, `color`, `position`, `wip_limit` — existing columns at that position shift right
- **Set WIP limit:** Advisory limit; frontend shows **red warning** when count exceeds limit (does not block moves)
- **Mark Done column:** When a task is moved to a column with `is_done_column = true`, the task's `completed_at` is auto-set
- **Reorder columns:** Positions are atomically updated to reflect the new sort order

---

## 4. Task Management (Core Domain)

**Module:** `apps/tasks` | **Models:** Task, Comment, Attachment, ActivityLog

### 4.1 Task Creation

| Step | What Happens |
|------|-------------|
| 1 | User sends `POST /api/v1/tasks/` with `project`, `title`, `description`, `priority`, `assignee`, `due_date`, `estimated_hours`, `tags` |
| 2 | A **task number** is auto-incremented per project (e.g., 1, 2, 3…) |
| 3 | A **task key** is generated: `{project_prefix}-{task_number}` (e.g., `WEB-42`) — unique and indexed |
| 4 | Default status is `BACKLOG`, reporter is set to the authenticated user |
| 5 | If an assignee is set, a `TASK_ASSIGNED` notification is sent |
| 6 | An `ActivityLog` entry with action `CREATED` is recorded |

**Task statuses:** `BACKLOG` | `TODO` | `IN_PROGRESS` | `IN_REVIEW` | `DONE` | `CANCELLED`
**Task priorities:** `CRITICAL` | `HIGH` | `MEDIUM` | `LOW`

### 4.2 Subtasks

- Create a subtask by setting the `parent` field to another task's ID
- The parent task exposes a `subtask_count` property
- Subtasks are nested in the task detail view

### 4.3 Task Listing & Filtering

**Pagination:** 25 tasks per page with `count`, `next`, `previous`, `results`

| Filter Parameter | Description |
|------------------|-------------|
| `status` | Filter by status (e.g., `IN_PROGRESS`) |
| `priority` | Filter by priority (e.g., `HIGH`) |
| `assignee` | Filter by assignee user ID |
| `is_overdue` | `true` — tasks past `due_date` that are not DONE |
| `tags` | Filter by tag name (uses PostgreSQL GIN index) |
| `due_date_gte` / `due_date_lte` | Date range filter |
| `search` | Keyword search in title and description |
| `column` | Filter by board column ID |

### 4.4 Task Update & Activity Tracking

| Event | What Happens |
|-------|-------------|
| **Any field change** | An `ActivityLog` entry records: `user`, `action`, `field_name`, `old_value`, `new_value`, `timestamp` |
| **Assignee changed** | A `TASK_ASSIGNED` notification is sent to the new assignee |
| **Status → IN_PROGRESS** | `started_at` is automatically set to the current time |
| **Status → DONE** | `completed_at` is automatically set to the current time |
| **Any update on board** | Change is broadcast via **WebSocket** to all board subscribers |

**Frontend inline editing:**
- Double-click the title → editable input, press Enter to save
- Click description area → textarea appears, click "Save" to submit

### 4.5 Tags

- Stored in a PostgreSQL `ArrayField` with **GIN index** for fast lookup
- Add/remove tags by updating the `tags` array via PATCH

### 4.6 Time Tracking

- Each task has `estimated_hours` and `logged_hours` (decimal fields)
- The task detail sidebar shows both values side by side

### 4.7 Soft Delete

- `DELETE /api/v1/tasks/{id}/` sets `deleted_at` (not physically removed)
- Soft-deleted tasks no longer appear in default listings
- Data remains in the database for audit purposes

### 4.8 Comments (Threaded)

| Step | What Happens |
|------|-------------|
| 1 | `POST /api/v1/tasks/{id}/comments/` with `content` (and optional `parent` for replies) |
| 2 | Comment is linked to the task; if `parent` is set, it forms a thread |
| 3 | The task assignee receives a `COMMENT_ADDED` notification |
| 4 | Comments display in chronological order with author avatar, name, relative timestamp, and content |

### 4.9 Attachments

| Step | What Happens |
|------|-------------|
| 1 | Upload a file to `POST /api/v1/tasks/{id}/attachments/` |
| 2 | Backend validates file size (max **10 MB**) — larger files are rejected with `400` |
| 3 | Attachment record stores `filename`, `file_size`, `content_type`, `uploaded_by` |
| 4 | An `ActivityLog` with action `ATTACHMENT_ADDED` is created |
| 5 | Files are stored via the configured storage backend (local / S3) |

### 4.10 Activity Log (Audit Trail)

- `GET /api/v1/tasks/{id}/activity/` returns the full audit trail in reverse chronological order
- Each entry includes: **user**, **action** (CREATED, ASSIGNED, STATUS_CHANGED, PRIORITY_CHANGED, COMMENTED, ATTACHMENT_ADDED, MOVED), **old/new values**, **timestamp**
- The frontend renders this as a vertical timeline with relative timestamps

---

## 5. Kanban Board (Drag & Drop)

**Module:** Frontend `features/board` + Backend `apps/tasks` (move endpoint)
**Tech:** Angular CDK DragDrop + Django Channels WebSocket

### 5.1 Board Layout

| Element | Description |
|---------|-------------|
| **Kanban container** | Horizontally scrollable, one lane per column |
| **Column header** | Column name + color indicator (8px circle) + task count badge |
| **WIP indicator** | Displays "WIP: N" if a limit is set; turns **red** when exceeded |
| **Task cards** | Vertically stacked, draggable via CDK `cdkDrag` |

Tasks are loaded via `GET /api/v1/tasks/?board={board_id}&page_size=200&ordering=position` and grouped by `column_id`.

### 5.2 Task Card Contents

Each card shows: **task key** (muted), **priority badge** (colored icon), **title**, **subtask count** (icon + count), **comment count**, **due date** (red if overdue), **assignee avatar** (initials fallback). Clicking a card navigates to the task detail page.

### 5.3 Drag & Drop — Within Same Column

| Step | What Happens |
|------|-------------|
| 1 | User drags a task card to a new position within the same column |
| 2 | CDK fires a `DragDrop` event (same container, different index) |
| 3 | Frontend calls `moveItemInArray` for instant local reorder |
| 4 | A `PATCH` request updates the task position on the backend |

### 5.4 Drag & Drop — Between Columns

| Step | What Happens |
|------|-------------|
| 1 | User drags a task card from one column to another |
| 2 | CDK fires a `DragDrop` event (different containers) |
| 3 | Frontend calls `transferArrayItem` for optimistic UI update |
| 4 | `POST /api/v1/tasks/{id}/move/` is sent with `column_id` and `position` |
| 5 | Backend updates the task's column, position, and auto-sets `started_at` or `completed_at` based on column type |
| 6 | An `ActivityLog` with action `MOVED` is created |
| 7 | The change is **broadcast via WebSocket** to all board viewers |

**Moving to the "Done" column:**
- `completed_at` is auto-set
- Status updates to `DONE`
- Assignee receives a `TASK_COMPLETED` notification

**Error handling:** If the API call fails, a toast error "Failed to move task" appears.

### 5.5 Bulk Move

- Select multiple tasks → `POST /api/v1/tasks/bulk-move/` with `task_ids[]` and `column_id`
- All tasks are moved **atomically** in a single transaction

### 5.6 WIP Limits

- WIP limits are **advisory** — they do not block moves
- When a column exceeds its limit, the WIP badge turns red (`text-danger`) as a visual warning
- This encourages teams to finish work before pulling more in

### 5.7 Connected Drop Lists

- All columns on a board are registered as connected `cdkDropList` instances
- Any task can be dragged from any column to any other column

### 5.8 Add Column

- Click "+ Column" in the board header → enter column name in a prompt dialog
- `POST` creates the column at the end of the board
- The new column appears immediately with a success toast

### 5.9 Real-Time Updates via WebSocket

| Step | What Happens |
|------|-------------|
| 1 | When a user opens a board page, a WebSocket connects to `ws/board/{board_id}/` with JWT token |
| 2 | When any user on the team moves or updates a task, the backend broadcasts a `task_update` message via Django Channels |
| 3 | All connected clients receive the message and reload the board |
| 4 | When the user navigates away, the WebSocket is disconnected in `ngOnDestroy` |

---

## 6. Notifications System

**Module:** `apps/notifications` | **Delivery:** In-App + WebSocket (real-time) + Email (Celery)

### 6.1 Notification Types

| Type | Trigger |
|------|---------|
| `TASK_ASSIGNED` | Task assignee field changes → notify new assignee |
| `TASK_UPDATED` | Any field change on a watched task → notify watchers |
| `TASK_COMPLETED` | Status changes to DONE → notify reporter |
| `COMMENT_ADDED` | New comment on an assigned task → notify assignee |
| `MENTION` | @mention in a comment → notify mentioned user |
| `DUE_DATE_REMINDER` | Celery beat fires daily at 8:00 AM → tasks due tomorrow |
| `PROJECT_INVITATION` | User added as project member → notify invitee |
| `SYSTEM` | System-level admin broadcasts |

### 6.2 In-App Notification Generation

| Step | What Happens |
|------|-------------|
| 1 | A Django **signal** (`post_save`) fires when a relevant model changes |
| 2 | A `Notification` record is created with: `recipient`, `sender`, `notification_type`, `title`, `message`, `is_read=false`, and a `GenericForeignKey` to the related object |
| 3 | The notification is immediately sent to the recipient's **WebSocket channel** |

### 6.3 Celery Periodic Tasks

| Task | Schedule | What Happens |
|------|----------|-------------|
| **Due date reminders** | Daily at 8:00 AM | Finds tasks due tomorrow → creates `DUE_DATE_REMINDER` notifications + sends emails |
| **Overdue notifications** | Daily at 9:00 AM | Finds overdue incomplete tasks → creates overdue notifications + emails |
| **Cleanup old notifications** | Periodic | Deletes **read** notifications older than 90 days |

### 6.4 Real-Time WebSocket Delivery

| Step | What Happens |
|------|-------------|
| 1 | Angular app connects to `ws/notifications/?token={jwt_access_token}` on startup |
| 2 | The `JWTAuthMiddleware` validates the token from the query parameter, sets the user on the scope |
| 3 | The user is added to a personal notification group |
| 4 | When a new notification is created, Django Channels `NotificationConsumer` serializes it to JSON and sends it to the user's group |
| 5 | Angular receives the message → prepends it to the notification list → increments the unread count |
| 6 | **Invalid/expired token** → WebSocket is rejected (close code 4001) |

### 6.5 Notification List (Frontend)

- Navigate to `/notifications` to view all notifications in reverse chronological order
- Each notification shows: **type icon** (contextual Bootstrap icon), **title** (bold), **relative timestamp**, **message text**, **unread indicator** (blue dot, `bg-light` background)

**Notification icons by type:**

| Type | Icon | Color |
|------|------|-------|
| TASK_ASSIGNED | `bi-person-check` | primary |
| TASK_UPDATED | `bi-pencil-square` | info |
| TASK_COMPLETED | `bi-check-circle` | success |
| COMMENT_ADDED | `bi-chat-left-text` | secondary |
| MENTION | `bi-at` | warning |
| DUE_DATE_REMINDER | `bi-clock` | warning |
| Overdue | `bi-exclamation-triangle` | danger |
| PROJECT_INVITATION | `bi-envelope` | primary |

### 6.6 Notification Actions

| Action | How It Works |
|--------|-------------|
| **Mark as read** | Click a notification → `POST /notifications/{id}/mark-read/` → sets `read_at`, removes blue dot, decrements unread count |
| **Mark all as read** | Click "Mark all read" → `POST /notifications/mark-all-read/` → sets `read_at` on all, resets count to 0, shows success toast |
| **Clear read** | Click "Clear read" → `DELETE /notifications/clear-read/` → removes read notifications from the list |
| **Load more** | Pagination — click "Load more" to fetch the next page (25 per page); button hides when no more pages |

### 6.7 Header Bell

- The header bell icon shows an **unread badge** with the current count
- The count is **polled every 30 seconds** and updated in real-time via WebSocket
- Clicking the bell navigates to `/notifications`

### 6.8 Email Notifications

- Emails are sent via **Celery background tasks** (non-blocking)
- Task assignment, due date reminders, and welcome emails all use this path
- Each email includes a direct link to the relevant item

---

## 7. Reports & Analytics Dashboard

**Module:** `apps/reports` (backend) + `features/reports` (frontend)
**Charts:** `@swimlane/ngx-charts` (pie, bar-vertical, bar-horizontal, line)

### 7.1 Project Summary (KPI Cards)

Endpoint: `GET /api/v1/projects/{id}/reports/summary/`

| KPI Card | Value | Color |
|----------|-------|-------|
| **Total Tasks** | Count of non-deleted tasks | primary (blue) |
| **Completed** | Tasks with status DONE | success (green) |
| **Overdue** | Past due_date and not done | danger (red) |
| **Completion %** | `(completed / total) × 100` (1 decimal) | default |

Additional metrics: **average cycle time** (hours from `started_at` to `completed_at` across all completed tasks).

### 7.2 Tasks by Status (Doughnut Chart)

- Endpoint: `GET /reports/tasks-by-status/`
- Rendered as a **doughnut/pie chart** with `ngx-charts-pie-chart`
- Color scheme matches column colors: gray (Backlog), blue (To Do), yellow (In Progress), cyan (In Review), green (Done)

### 7.3 Tasks by Priority (Vertical Bar Chart)

- Endpoint: `GET /reports/tasks-by-priority/`
- Rendered as a **vertical bar chart** with `ngx-charts-bar-vertical`
- Color scheme: gray (Low), blue (Medium), yellow (High), red (Critical)

### 7.4 Burndown Chart (Line Chart)

- Endpoint: `GET /reports/burndown/?days=30`
- Shows **remaining tasks over 30 days**, accounting for scope creep (new tasks created daily)
- Formula: `remaining = yesterday_remaining + new_tasks - completed_tasks`
- Rendered as a **line chart** with timeline enabled

### 7.5 Velocity Chart (Bar Chart)

- Endpoint: `GET /reports/velocity/?weeks=12`
- Shows **tasks completed per week** over 12 weeks
- Rendered as a vertical bar chart

### 7.6 Assignee Workload (Horizontal Bar Chart)

- Endpoint: `GET /reports/tasks-by-assignee/`
- Shows per-assignee metrics: `total`, `completed`, `in_progress`
- Chart height dynamically adjusts: `max(200, assigneeCount × 40)` pixels

### 7.7 Additional Reports

| Report | Endpoint | Description |
|--------|----------|-------------|
| **Tasks by Label** | `GET /reports/tasks-by-label/` | Tag frequency from PostgreSQL `ArrayField` using `unnest(tags)` |
| **Activity Heatmap** | `GET /reports/activity-heatmap/?days=90` | Daily activity counts from `ActivityLog` |
| **Monthly Throughput** | `GET /reports/monthly-throughput/?months=12` | Tasks completed per month over 12 months |

### 7.8 CSV Export

| Step | What Happens |
|------|-------------|
| 1 | User clicks "Export CSV" on the reports page |
| 2 | `GET /reports/export-csv/` → backend `ReportService.export_tasks_csv()` queries all non-deleted project tasks |
| 3 | CSV is generated with headers: Task Key, Title, Status, Priority, Assignee, Reporter, Due Date, Created, Completed, Column, Tags, Story Points |
| 4 | Frontend creates a `Blob`, generates an object URL, triggers a download as `project-{id}-tasks.csv` |
| 5 | Object URL is revoked; success toast "Export downloaded" appears |
| 6 | On failure, error toast "Export failed" appears |

---

## 8. Admin Panel

**Module:** `features/admin` | **Pages:** Organization Settings, Member Management

### 8.1 Organization Settings

| Step | What Happens |
|------|-------------|
| 1 | Navigate to `/admin` → loads `OrgSettingsComponent` |
| 2 | Breadcrumb shows: Dashboard > Organization Settings |
| 3 | A form displays current org data (name, description) |
| 4 | Edit fields and click "Save Changes" → `PATCH /api/v1/organizations/{id}/` |
| 5 | Button shows "Saving..." during request; success toast on completion |
| 6 | "Manage Members" button navigates to `/admin/members` |

### 8.2 Member Management

| Step | What Happens |
|------|-------------|
| 1 | Navigate to `/admin/members` → breadcrumb: Dashboard > Settings > Members |
| 2 | A table lists all members: **Avatar + Name + Email**, **Role dropdown** (OWNER/ADMIN/MEMBER), **Joined date**, **Remove button** |
| 3 | OWNER role dropdown is **disabled** (cannot be changed); remove button is hidden for OWNER |

**Invite a member:**
| Step | What Happens |
|------|-------------|
| 1 | Click "Invite" → form appears with email input and role select (default: MEMBER) |
| 2 | Enter email, select role, click "Send" → `POST /api/v1/organizations/{id}/members/` |
| 3 | Success: toast "Member invited", form closes, list refreshes |
| 4 | Failure: toast "Failed to invite member" |

**Change role inline:**
- Select a new role in the dropdown → `PATCH` updates the membership → toast "Role updated"

**Remove member:**
| Step | What Happens |
|------|-------------|
| 1 | Click the trash icon → a **ConfirmDialog** modal appears: "Are you sure you want to remove this member?" |
| 2 | Click "Remove" (red button) → `DELETE` removes the member → toast "Member removed" |
| 3 | Click "Cancel" → dialog closes, no action taken |

---

## 9. Layout, Navigation & Shared Components

**Module:** `layout/` + `shared/`

### 9.1 Shell Layout

- **Authenticated users** see the full shell: Sidebar (left) + Header (top) + Router outlet (main content) + Toast overlay (bottom-right)
- **Unauthenticated users** see only the auth pages (login, register) without the shell
- The sidebar can be **collapsed** to icon-only width via a toggle button; collapse state is stored in a signal

### 9.2 Header Component

| Element | Behavior |
|---------|----------|
| **Search input** | Placeholder "Search tasks, projects..." |
| **Notification bell** | Badge with unread count, polled every 30s + real-time WebSocket updates; click navigates to `/notifications` |
| **User avatar dropdown** | Options: My Profile, Settings (`/admin`), Sign Out (calls `AuthService.logout()`) |

### 9.3 Sidebar Component

| Navigation Item | Icon | Route |
|----------------|------|-------|
| Dashboard | `bi-speedometer2` | `/dashboard` |
| Projects | `bi-folder2` | `/projects` |
| Notifications | `bi-bell` | `/notifications` |
| Settings | `bi-gear` | `/admin` |

- **Active route** is highlighted with the `active` CSS class
- **Organization selector** at the top shows the currently selected org (supports multiple orgs)
- **Responsive:** Collapses automatically on viewports < 768px; toggle button available

### 9.4 Dashboard

| Section | Content |
|---------|---------|
| **Stats cards** | Total Projects, Total Tasks, In Progress, Overdue |
| **Recent Projects** | Latest projects with names |
| **My Tasks** | Tasks assigned to the current user with priority and status badges |

### 9.5 Shared Components

| Component | Purpose | Key Features |
|-----------|---------|-------------|
| **LoadingSpinner** | Shows during async operations | Sizes: sm / md / lg; optional message; configurable min-height |
| **ConfirmDialog** | Modal for destructive actions | Custom title, message, confirm button label and CSS class; emits `confirmed` or `cancelled` |
| **UserAvatar** | Displays user identity | Shows image if URL exists, otherwise initials with deterministic background color; sizes: 24px / 32px / 48px |
| **PriorityBadge** | Colored priority indicator | CRITICAL=red triangle, HIGH=orange arrow-up, MEDIUM=blue dash, LOW=gray arrow-down |
| **StatusBadge** | Colored status label | BACKLOG=secondary, TODO=primary, IN_PROGRESS=warning, IN_REVIEW=info, DONE=success, CANCELLED=dark |
| **EmptyState** | Placeholder for empty lists | Large icon, title, subtitle, content projection for CTA button |
| **ToastContainer** | Notification toasts | Types: success (green), error (red), warning (yellow), info (blue); auto-dismiss; signal-based queue |

### 9.6 Shared Pipes

| Pipe | Input → Output |
|------|----------------|
| **TimeAgo** | Date → "just now", "3 minutes ago", "2 hours ago", "1 day ago", "5 days ago", "1 month ago", "1 year ago" |
| **Truncate** | Long text + limit → "This is a very long ..." |

### 9.7 Route Guards

| Guard | Behavior |
|-------|----------|
| **authGuard** | Blocks unauthenticated users from protected routes → redirects to `/auth/login`. During initial loading (`AuthService.isLoading`), polls every 50ms for up to 5 seconds before deciding. |
| **guestGuard** | Redirects authenticated users away from auth pages → navigates to `/dashboard` |

### 9.8 404 Not Found

- Navigating to any unknown route shows the `NotFoundComponent`
- Displays: large "404" heading, "Page not found" message, "Back to Dashboard" button

---

## 10. Infrastructure, Deployment & Security

### 10.1 Docker Compose — Development

Command: `docker compose up -d`

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **postgres** | postgres:17-alpine | 5432 | PostgreSQL database with health check (`pg_isready`) |
| **redis** | redis:7.4-alpine | 6379 | 3 databases: db0=Django cache, db1=Celery broker+results, db2=Channels layer. Health check: `redis-cli ping` |
| **backend** | ./backend Dockerfile | 8000 | Django + Daphne (HTTP + WebSocket). Depends on postgres + redis being healthy |
| **celery-worker** | ./backend Dockerfile | — | Background task processor |
| **celery-beat** | ./backend Dockerfile | — | Periodic task scheduler |
| **frontend** | node:22-alpine | 4200 | Angular dev server with hot reload (`ng serve --host 0.0.0.0 --poll 2000`) |

**Persistent volumes:** `postgres_data`, `redis_data`, `backend_static`, `backend_media`, `frontend_node_modules`

### 10.2 Docker Compose — Production

| Difference | Details |
|-----------|---------|
| **Redis** | Requires password (`--requirepass`) |
| **Backend** | Pre-built image from container registry; 2 replicas with resource limits (512M memory, 0.5 CPU) |
| **Celery worker** | 2 replicas with resource limits |
| **Nginx** | Added as reverse proxy with SSL |
| **Certbot** | Automatic Let's Encrypt certificate renewal |
| **Secrets** | All via `.env` file: `SECRET_KEY`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `AWS_ACCESS_KEY_ID`, `SENTRY_DSN`, etc. |

### 10.3 Backend Dockerfile (Multi-Stage)

| Stage | Base Image | Purpose |
|-------|-----------|---------|
| **builder** | python:3.12-slim | Install dependencies, compile packages |
| **runtime** | python:3.12-slim | Lean production image with non-root user `appuser` and health check |

**Entrypoint commands:** `server` (Daphne), `worker` (Celery worker with autoscale), `beat` (Celery beat), `flower` (monitoring), `migrate`, `createsuperuser`, `shell`, `test` (pytest)

### 10.4 Nginx Configuration

**Routing:**

| Path | Destination | Notes |
|------|-------------|-------|
| `/api/*` | backend:8000 | Rate limit: 30 req/sec |
| `/api/v1/auth/*` | backend:8000 | Rate limit: 5 req/min |
| `/ws/*` | backend:8000 | WebSocket upgrade (HTTP/1.1, 24h timeout) |
| `/admin/*` | backend:8000 | Django admin |
| `/static/*` | Nginx static | 30-day cache |
| `/media/*` | Nginx static | 7-day cache |
| `/*` | Angular SPA | `index.html` fallback |
| `/.well-known/acme-challenge/*` | certbot | Let's Encrypt |

**Hashed assets** (`*.[hash].(js|css)`) get 1-year cache with `Cache-Control: public, immutable`.

**Security headers:** `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Strict-Transport-Security: max-age=31536000; includeSubDomains`, `Content-Security-Policy`

**SSL:** TLSv1.2 + TLSv1.3, shared session cache, HTTP→HTTPS 301 redirect

### 10.5 GitHub Actions — CI Pipeline

**Triggers:** Push to `main`/`develop`, Pull requests to `main`

| Job | Steps |
|-----|-------|
| **backend-lint** | Checkout → Python 3.12 → Install dev deps → `ruff check .` → `ruff format --check .` |
| **backend-type-check** | Checkout → Python 3.12 → Install dev deps → `mypy apps/` |
| **backend-test** | Start PostgreSQL 17 + Redis 7.4 services → Checkout → Install deps → Run migrations → `pytest --cov --cov-report=xml -v` → Upload coverage to Codecov |
| **frontend-lint** | `npx ng lint` |
| **frontend-test** | `npx ng test --watch=false --browsers=ChromeHeadless --code-coverage` |
| **frontend-build** | `npx ng build --configuration=production` → Upload build artifact |
| **docker-build** | Only on `main` after tests pass → Docker Buildx → Login to ghcr.io → Build + push `backend:latest` and `backend:{sha}` → GitHub Actions cache for layers |

### 10.6 GitHub Actions — Deploy Pipeline

| Step | What Happens |
|------|-------------|
| 1 | Triggers after CI succeeds on `main` |
| 2 | Uses concurrency group to prevent parallel deploys |
| 3 | SSH into production server |
| 4 | Pull latest code + Docker images |
| 5 | Run database migrations |
| 6 | Collect static files |
| 7 | Restart services: `docker compose up -d` |
| 8 | Prune old Docker images |
| 9 | Health check: `GET https://{host}/api/v1/health/` → expect HTTP 200 |
| 10 | On failure: Slack notification |

### 10.7 Django Security Settings (Production)

| Setting | Value |
|---------|-------|
| `SECURE_SSL_REDIRECT` | `True` |
| `SECURE_HSTS_SECONDS` | 31536000 (1 year) |
| `SECURE_HSTS_SUBDOMAINS` | `True` |
| `SECURE_HSTS_PRELOAD` | `True` |
| `SESSION_COOKIE_SECURE` | `True` |
| `CSRF_COOKIE_SECURE` | `True` |
| `SESSION_COOKIE_HTTPONLY` | `True` |
| `SECURE_CONTENT_TYPE_NOSNIFF` | `True` |
| `SECURE_BROWSER_XSS_FILTER` | `True` |

### 10.8 API Throttling

| Throttle Class | Rate | Scope |
|---------------|------|-------|
| AnonRateThrottle | 100/hour | Unauthenticated users |
| UserRateThrottle | 1000/hour | Authenticated users |
| LoginRateThrottle | 5/minute | Login endpoint |
| PasswordResetThrottle | 3/hour | Password reset |

### 10.9 CORS Configuration

| Setting | Value |
|---------|-------|
| `CORS_ALLOWED_ORIGINS` | Explicit list of frontend origins |
| `CORS_ALLOW_CREDENTIALS` | `True` (required for HttpOnly cookie) |
| `CORS_ALLOWED_HEADERS` | Authorization, Content-Type, etc. |

---

## Summary

| Module | Features | Scenarios |
|--------|----------|-----------|
| Authentication | Registration, Login, JWT Refresh, Logout, Profile, Password | 15 |
| Organizations | CRUD, Slugs, Members, Roles, Permissions | 12 |
| Projects | Projects, Boards, Columns, WIP, Archive/Restore | 15 |
| Tasks | Tasks, Subtasks, Filtering, Comments, Attachments, Activity | 22 |
| Kanban Board | Drag-Drop, Move, Bulk Move, WIP Limits, WebSocket | 14 |
| Notifications | Signals, Celery, WebSocket, UI Actions, Email | 16 |
| Reports | KPIs, Charts, Burndown, Velocity, CSV Export | 12 |
| Admin Panel | Org Settings, Member Management | 8 |
| Layout & Shared | Shell, Header, Sidebar, Dashboard, Components, Guards, 404 | 18 |
| Infrastructure | Docker, Nginx, CI/CD, Security | 20 |
| **Total** | | **~152 scenarios** |
