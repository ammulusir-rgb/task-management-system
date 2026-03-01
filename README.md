# Task Manager — Enterprise SaaS

Production-ready, scalable Task Management application built with **Angular 21**, **Django 5.2 LTS**, **PostgreSQL 17**, **Redis 7.4**, **Celery**, and **Django Channels**.

---

## Architecture

```
┌────────────────┐     ┌─────────────────┐     ┌──────────┐
│  Angular 21    │────▶│  Django 5.2 LTS │────▶│ PostgreSQL│
│  (Bootstrap 5) │     │  DRF + Channels │     │    17     │
└────────────────┘     └────────┬────────┘     └──────────┘
                                │
                       ┌────────┴────────┐
                       │     Redis 7.4   │
                       │ Cache│Celery│WS │
                       └─────────────────┘
```

**Key Features:**
- Multi-tenant organizations with role-based access (Owner / Admin / Member / Viewer)
- Projects with Kanban boards, customizable columns, WIP limits
- Tasks with subtasks, comments, attachments, activity logs, tags, time tracking
- Real-time updates via WebSocket (Django Channels)
- Background jobs via Celery (email notifications, due-date reminders, reports)
- Interactive reports with @swimlane/ngx-charts (burndown, velocity, workload)
- JWT authentication — access token in memory, refresh token in HttpOnly cookie
- Docker Compose for dev & production, Nginx reverse proxy, GitHub Actions CI/CD

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Angular 21, TypeScript 5.8, Bootstrap 5, ngx-bootstrap, CDK Drag & Drop, ngx-charts |
| Backend | Django 5.2 LTS, Django REST Framework 3.16, SimpleJWT 5.5, drf-spectacular |
| Database | PostgreSQL 17 (GIN indexes, partial indexes, ArrayField) |
| Cache | Redis 7.4 (db0=cache, db1=Celery, db2=Channels) |
| Task Queue | Celery 5.6 with Redis broker |
| WebSocket | Django Channels 4.3, Daphne 4.2 |
| Infrastructure | Docker, Nginx, GitHub Actions, Let's Encrypt |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose v2
- Git

### 1. Clone & Start

```bash
git clone <repo-url> && cd Saas
docker compose up -d
```

### 2. Run Migrations & Create Admin

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

### 3. Access

| Service | URL |
|---------|-----|
| Frontend | http://localhost:4200 |
| Backend API | http://localhost:8000/api/v1/ |
| API Docs (Swagger) | http://localhost:8000/api/docs/ |
| Django Admin | http://localhost:8000/admin/ |

---

## Project Structure

```
Saas/
├── backend/
│   ├── apps/
│   │   ├── common/          # Shared mixins, pagination, exceptions, middleware
│   │   ├── users/           # Auth, JWT, user management
│   │   ├── organizations/   # Multi-tenant orgs, members, roles
│   │   ├── projects/        # Projects, boards, columns
│   │   ├── tasks/           # Tasks, comments, attachments, activity
│   │   ├── notifications/   # In-app + WebSocket notifications
│   │   └── reports/         # Analytics, charts data, CSV export
│   ├── config/              # Settings (base/dev/prod/test), URLs, ASGI, Celery
│   ├── tests/               # pytest tests with factories
│   ├── requirements/        # base.txt, dev.txt, prod.txt
│   ├── Dockerfile
│   └── entrypoint.sh
├── frontend/
│   └── src/app/
│       ├── core/            # Services, interceptors, guards, models
│       ├── shared/          # Reusable components, pipes, toast service
│       ├── layout/          # Shell, header, sidebar
│       └── features/        # Auth, dashboard, projects, board, tasks,
│                            # reports, admin, notifications
├── nginx/
│   └── nginx.conf
├── .github/workflows/       # CI + Deploy pipelines
├── docker-compose.yml       # Development
└── docker-compose.prod.yml  # Production
```

---

## Development

### Backend (without Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements/dev.txt
cp ../.env.example .env  # configure DATABASE_URL, REDIS_URL, SECRET_KEY
python manage.py migrate
python manage.py runserver
```

### Frontend (without Docker)

```bash
cd frontend
npm install --legacy-peer-deps
npx ng serve
```

### Running Tests

```bash
# Backend
cd backend && pytest -v --cov

# Frontend
cd frontend && npx ng test --watch=false --code-coverage
```

### Linting

```bash
# Backend
ruff check backend/ && ruff format --check backend/

# Frontend
cd frontend && npx ng lint
```

---

## API Overview

All endpoints are under `/api/v1/`:

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/auth/register/` | POST | User registration |
| `/auth/token/` | POST | Login (returns access + sets refresh cookie) |
| `/auth/token/refresh/` | POST | Refresh via HttpOnly cookie |
| `/auth/logout/` | POST | Blacklist refresh token |
| `/users/me/` | GET, PATCH | Current user profile |
| `/organizations/` | CRUD | Organization management |
| `/organizations/:id/members/` | GET, POST, PATCH, DELETE | Member management |
| `/projects/` | CRUD | Projects with archive/restore |
| `/projects/:id/boards/` | CRUD | Kanban boards |
| `/projects/:id/boards/:id/columns/` | CRUD | Board columns |
| `/tasks/` | CRUD | Tasks with filtering & search |
| `/tasks/:id/move/` | POST | Move task between columns |
| `/tasks/:id/comments/` | GET, POST | Task comments |
| `/tasks/:id/attachments/` | GET, POST | File attachments |
| `/tasks/:id/activity/` | GET | Activity log |
| `/notifications/` | GET | User notifications |
| `/projects/:id/reports/summary/` | GET | Project analytics |
| `/projects/:id/reports/burndown/` | GET | Burndown chart data |
| `/projects/:id/reports/velocity/` | GET | Velocity metrics |
| `/projects/:id/reports/export-csv/` | GET | CSV export |

Full OpenAPI schema: `GET /api/schema/`

---

## WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `ws/notifications/` | Real-time user notifications |
| `ws/board/<board_id>/` | Board-level task updates |

Connect with token: `ws://host/ws/notifications/?token=<jwt_access_token>`

---

## Environment Variables

See [.env.example](backend/.env.example) for all available configuration.

Key variables:
- `SECRET_KEY` — Django secret key
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `CORS_ALLOWED_ORIGINS` — Allowed frontend origins
- `ALLOWED_HOSTS` — Django allowed hosts

---

## Production Deployment

```bash
# Build frontend
cd frontend && npx ng build --configuration=production

# Deploy with production compose
docker compose -f docker-compose.prod.yml up -d

# SSL setup (first time)
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot -w /var/www/certbot -d yourdomain.com
```

---

## License

MIT
