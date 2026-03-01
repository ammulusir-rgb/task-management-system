# =============================================================================
# Feature 10: Infrastructure — Docker, CI/CD, Nginx, Security
# Module: docker-compose.yml, .github/workflows, nginx/nginx.conf
# =============================================================================

@infrastructure
Feature: Infrastructure, Deployment and Security
  As a DevOps engineer
  I want containerized services, CI/CD pipelines, and production-grade configuration
  So that the application is reliably built, tested, and deployed

  # ---------------------------------------------------------------------------
  # Docker Compose — Development
  # ---------------------------------------------------------------------------
  @docker @dev
  Scenario: Development environment with Docker Compose
    Given the file "docker-compose.yml" exists at the project root
    When I run "docker compose up -d"
    Then the following services should start:
      | Service        | Image               | Port  | Description                        |
      | postgres       | postgres:17-alpine  | 5432  | PostgreSQL database                |
      | redis          | redis:7.4-alpine    | 6379  | Cache, Celery broker, Channels     |
      | backend        | ./backend Dockerfile| 8000  | Django + Daphne (HTTP + WS)        |
      | celery-worker  | ./backend Dockerfile| -     | Background task processor          |
      | celery-beat    | ./backend Dockerfile| -     | Periodic task scheduler            |
      | frontend       | node:22-alpine      | 4200  | Angular dev server (ng serve)      |

  @docker @dev
  Scenario: PostgreSQL health check
    Then the postgres service should have a healthcheck:
      | Property | Value                            |
      | test     | pg_isready -U taskmanager        |
      | interval | 5s                               |
      | timeout  | 5s                               |
      | retries  | 5                                |
    And dependent services should wait for postgres to be healthy

  @docker @dev
  Scenario: Redis health check
    Then the redis service should have a healthcheck:
      | Property | Value          |
      | test     | redis-cli ping |
      | interval | 5s             |
      | timeout  | 5s             |
      | retries  | 5              |

  @docker @dev
  Scenario: Backend service configuration
    Then the backend service should:
      | Aspect          | Detail                                     |
      | Command         | "server" (via entrypoint.sh)               |
      | Settings module | config.settings.development                |
      | Database        | postgres://taskmanager:...@postgres:5432    |
      | Redis databases | db0=cache, db1=Celery, db2=Channels        |
      | Volume mounts   | Source code, static files, media files     |
      | Depends on      | postgres (healthy), redis (healthy)        |

  @docker @dev
  Scenario: Frontend dev server with hot reload
    Then the frontend service should:
      | Aspect  | Detail                                         |
      | Command | npm install && npx ng serve --host 0.0.0.0     |
      | Port    | 4200                                           |
      | Volume  | ./frontend mounted with node_modules volume    |
      | Poll    | --poll 2000 for file watching in Docker        |

  @docker @dev
  Scenario: Persistent volumes
    Then the following named volumes should be used:
      | Volume                 | Purpose                       |
      | postgres_data          | PostgreSQL data persistence   |
      | redis_data             | Redis data persistence        |
      | backend_static         | Django collected static files |
      | backend_media          | User-uploaded files           |
      | frontend_node_modules  | npm packages cache            |

  # ---------------------------------------------------------------------------
  # Docker Compose — Production
  # ---------------------------------------------------------------------------
  @docker @prod
  Scenario: Production environment with Docker Compose
    Given the file "docker-compose.prod.yml" exists
    Then it should include:
      | Service        | Difference from Dev                        |
      | postgres       | Uses env vars for credentials              |
      | redis          | Requires password (--requirepass)          |
      | backend        | Uses pre-built image from registry         |
      | celery-worker  | 2 replicas with resource limits            |
      | celery-beat    | Single instance                            |
      | nginx          | Reverse proxy with SSL                     |
      | certbot        | Automatic certificate renewal              |

  @docker @prod
  Scenario: Backend runs with replicas and resource limits
    Then the backend service should have:
      | Property          | Value       |
      | deploy.replicas   | 2           |
      | resources.memory  | 512M limit  |
      | resources.cpus    | 0.5 limit   |

  @docker @prod
  Scenario: Environment variables from .env file
    Then production secrets should be externalized:
      | Variable               | Description                    |
      | SECRET_KEY             | Django secret key              |
      | POSTGRES_PASSWORD      | Database password              |
      | REDIS_PASSWORD         | Redis authentication           |
      | ALLOWED_HOSTS          | Production domain(s)           |
      | CORS_ALLOWED_ORIGINS   | Frontend origin                |
      | AWS_ACCESS_KEY_ID      | S3 storage credentials         |
      | AWS_SECRET_ACCESS_KEY  | S3 storage credentials         |
      | SENTRY_DSN             | Error monitoring               |
      | DOCKER_REGISTRY        | Container registry URL         |
      | IMAGE_TAG              | Image version tag              |

  # ---------------------------------------------------------------------------
  # Backend Dockerfile (Multi-Stage)
  # ---------------------------------------------------------------------------
  @dockerfile
  Scenario: Backend Docker image build
    Given the backend Dockerfile uses multi-stage build:
      | Stage   | Base Image         | Purpose                        |
      | builder | python:3.12-slim   | Install deps, compile packages |
      | runtime | python:3.12-slim   | Lean production image          |
    Then the runtime image should:
      | Property        | Value                               |
      | User            | Non-root user "appuser"             |
      | Healthcheck     | curl localhost:8000/api/v1/health/  |
      | Working dir     | /app                                |

  @dockerfile
  Scenario: Entrypoint supports multiple commands
    Given the entrypoint.sh script is the Docker ENTRYPOINT
    Then it should support the following commands:
      | Command         | Action                                  |
      | server          | Wait for DB/Redis, then run Daphne      |
      | worker          | Start Celery worker with autoscale      |
      | beat            | Start Celery beat scheduler             |
      | flower          | Start Flower monitoring (port 5555)     |
      | migrate         | Run Django migrations                   |
      | createsuperuser | Create Django admin superuser           |
      | shell           | Open Django shell                       |
      | test            | Run pytest                              |

  # ---------------------------------------------------------------------------
  # Nginx Configuration
  # ---------------------------------------------------------------------------
  @nginx
  Scenario: Nginx reverse proxy configuration
    Given the file "nginx/nginx.conf" exists
    Then it should configure:
      | Feature                | Detail                                |
      | Worker processes       | auto                                  |
      | Worker connections     | 1024                                  |
      | Client max body size   | 10M                                   |
      | Gzip compression       | Enabled for text/css/js/json/xml/svg  |
      | HTTP → HTTPS redirect  | 301 redirect on port 80               |
      | SSL protocols          | TLSv1.2 TLSv1.3                       |
      | SSL session cache      | shared:SSL:10m                        |

  @nginx
  Scenario: Nginx routing configuration
    Then requests should be routed as follows:
      | Path Pattern                      | Destination              | Notes                    |
      | /api/*                            | backend:8000             | Rate limit: 30r/s        |
      | /api/v1/auth/*                    | backend:8000             | Rate limit: 5r/m         |
      | /ws/*                             | backend:8000 (WebSocket) | HTTP/1.1 Upgrade         |
      | /admin/*                          | backend:8000             | Django admin             |
      | /static/*                         | /usr/share/nginx/static/ | 30 day cache             |
      | /media/*                          | /usr/share/nginx/media/  | 7 day cache              |
      | /*                                | /usr/share/nginx/html/   | Angular SPA fallback     |
      | /.well-known/acme-challenge/*     | /var/www/certbot/        | Let's Encrypt            |

  @nginx
  Scenario: Security headers
    Then Nginx should add the following response headers:
      | Header                    | Value                                   |
      | X-Frame-Options           | DENY                                    |
      | X-Content-Type-Options    | nosniff                                 |
      | X-XSS-Protection          | 1; mode=block                           |
      | Referrer-Policy           | strict-origin-when-cross-origin         |
      | Strict-Transport-Security | max-age=31536000; includeSubDomains     |
      | Content-Security-Policy   | default-src 'self'; ...                 |

  @nginx
  Scenario: WebSocket proxy configuration
    Then the /ws/ location should configure:
      | Directive            | Value       |
      | proxy_http_version   | 1.1         |
      | Upgrade header       | $http_upgrade |
      | Connection header    | "upgrade"   |
      | proxy_read_timeout   | 86400 (24h) |

  @nginx
  Scenario: Angular hashed assets are cached aggressively
    Then files matching pattern "*.[0-9a-f]{16,}.(js|css)" should have:
      | Header        | Value                        |
      | expires       | 1 year                       |
      | Cache-Control | public, immutable            |

  # ---------------------------------------------------------------------------
  # GitHub Actions — Continuous Integration
  # ---------------------------------------------------------------------------
  @ci
  Scenario: CI pipeline runs on push and PR
    Given the file ".github/workflows/ci.yml" exists
    Then the CI workflow should trigger on:
      | Event        | Branches        |
      | push         | main, develop   |
      | pull_request | main            |

  @ci
  Scenario: Backend lint job
    Then a "backend-lint" job should:
      | Step                               |
      | Checkout code                      |
      | Setup Python 3.12 with pip cache   |
      | Install dev requirements           |
      | Run "ruff check ." (linting)       |
      | Run "ruff format --check ." (format check) |

  @ci
  Scenario: Backend type check job
    Then a "backend-type-check" job should:
      | Step                     |
      | Checkout code            |
      | Setup Python 3.12       |
      | Install dev requirements |
      | Run "mypy apps/"        |

  @ci
  Scenario: Backend test job with services
    Then a "backend-test" job should:
      | Step                                           |
      | Start PostgreSQL 17 service container          |
      | Start Redis 7.4 service container              |
      | Checkout code                                  |
      | Setup Python 3.12                              |
      | Install dev requirements                       |
      | Run migrations                                 |
      | Run "pytest --cov --cov-report=xml -v"         |
      | Upload coverage to Codecov                     |

  @ci
  Scenario: Frontend lint and test jobs
    Then a "frontend-lint" job should run "npx ng lint"
    And a "frontend-test" job should run "npx ng test --watch=false --browsers=ChromeHeadless --code-coverage"
    And a "frontend-build" job should run "npx ng build --configuration=production"
    And the build artifact should be uploaded for the deploy workflow

  @ci
  Scenario: Docker build and push on main branch
    Then a "docker-build" job should:
      | Step                                            |
      | Only run on main branch after tests pass        |
      | Setup Docker Buildx                             |
      | Login to GitHub Container Registry (ghcr.io)    |
      | Build and push backend image with tags:         |
      |   ghcr.io/{repo}/backend:latest                 |
      |   ghcr.io/{repo}/backend:{sha}                  |
      | Use GitHub Actions cache for Docker layers      |

  # ---------------------------------------------------------------------------
  # GitHub Actions — Deployment
  # ---------------------------------------------------------------------------
  @deploy
  Scenario: Automatic deployment on successful CI
    Given the file ".github/workflows/deploy.yml" exists
    Then the deploy workflow should:
      | Step                                             |
      | Trigger after CI workflow succeeds on main       |
      | Use concurrency group to prevent parallel deploys|
      | SSH into production server                       |
      | Pull latest code                                 |
      | Pull latest Docker images                        |
      | Run database migrations                          |
      | Collect static files                             |
      | Restart services with docker compose up -d       |
      | Prune old Docker images                          |
      | Run health check against /api/v1/health/         |
      | Notify Slack on failure                          |

  @deploy
  Scenario: Health check validation after deploy
    Given the deployment completes
    Then a health check should hit "https://{host}/api/v1/health/"
    And expect HTTP 200
    And if it fails, the pipeline should exit with error
    And a Slack notification should be sent on failure

  # ---------------------------------------------------------------------------
  # Django Settings — Security
  # ---------------------------------------------------------------------------
  @security
  Scenario: Production Django security settings
    Then the production settings should enable:
      | Setting                  | Value                          |
      | SECURE_SSL_REDIRECT      | True                           |
      | SECURE_HSTS_SECONDS      | 31536000                       |
      | SECURE_HSTS_SUBDOMAINS   | True                           |
      | SECURE_HSTS_PRELOAD      | True                           |
      | SESSION_COOKIE_SECURE    | True                           |
      | CSRF_COOKIE_SECURE       | True                           |
      | SESSION_COOKIE_HTTPONLY   | True                           |
      | SECURE_CONTENT_TYPE_NOSNIFF | True                        |
      | SECURE_BROWSER_XSS_FILTER| True                           |

  @security
  Scenario: API throttling in production
    Then the following rate limits should be enforced:
      | Throttle Class         | Rate      | Scope                 |
      | AnonRateThrottle       | 100/hour  | Unauthenticated users |
      | UserRateThrottle       | 1000/hour | Authenticated users   |
      | LoginRateThrottle      | 5/minute  | Login endpoint        |
      | PasswordResetThrottle  | 3/hour    | Password reset        |

  @security
  Scenario: CORS configuration
    Then CORS should be configured to:
      | Setting                  | Value                                |
      | CORS_ALLOWED_ORIGINS     | Explicit list of frontend origins    |
      | CORS_ALLOW_CREDENTIALS   | True (for HttpOnly cookie)           |
      | CORS_ALLOWED_HEADERS     | Authorization, Content-Type, etc.    |
