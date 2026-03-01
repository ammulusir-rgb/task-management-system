#!/bin/bash
set -euo pipefail

# ============================================================
# Backend Entrypoint Script
# Handles: migrations, server, celery worker, celery beat
# ============================================================

echo "==> Environment: ${DJANGO_SETTINGS_MODULE:-config.settings.production}"
echo "==> Command: ${1:-server}"

# Wait for dependent services
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local retries=30
    local count=0

    echo "==> Waiting for ${service} at ${host}:${port}..."
    while ! python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('${host}', ${port})); s.close()" 2>/dev/null; do
        count=$((count + 1))
        if [ $count -ge $retries ]; then
            echo "==> ERROR: ${service} not available after ${retries} attempts"
            exit 1
        fi
        echo "==> Waiting for ${service}... (${count}/${retries})"
        sleep 2
    done
    echo "==> ${service} is available"
}

# Wait for PostgreSQL
if [ -n "${DB_HOST:-}" ]; then
    wait_for_service "${DB_HOST}" "${DB_PORT:-5432}" "PostgreSQL"
fi

# Wait for Redis
if [ -n "${REDIS_HOST:-}" ]; then
    wait_for_service "${REDIS_HOST}" "${REDIS_PORT:-6379}" "Redis"
fi

case "${1:-server}" in
    server)
        echo "==> Running database migrations..."
        python manage.py migrate --noinput

        echo "==> Starting Daphne ASGI server on port ${PORT:-8000}..."
        exec daphne \
            -b 0.0.0.0 \
            -p "${PORT:-8000}" \
            --access-log - \
            --proxy-headers \
            config.asgi:application
        ;;

    worker)
        echo "==> Starting Celery worker..."
        exec celery -A config worker \
            --loglevel=info \
            --concurrency="${CELERY_CONCURRENCY:-4}" \
            --max-tasks-per-child=1000 \
            --without-heartbeat \
            -Q default,emails,notifications
        ;;

    beat)
        echo "==> Starting Celery Beat scheduler..."
        exec celery -A config beat \
            --loglevel=info \
            --scheduler django_celery_beat.schedulers:DatabaseScheduler
        ;;

    flower)
        echo "==> Starting Flower monitoring..."
        exec celery -A config flower \
            --port="${FLOWER_PORT:-5555}" \
            --broker_api="${CELERY_BROKER_URL:-redis://redis:6379/1}"
        ;;

    migrate)
        echo "==> Running database migrations..."
        exec python manage.py migrate --noinput
        ;;

    createsuperuser)
        echo "==> Creating superuser..."
        exec python manage.py createsuperuser
        ;;

    shell)
        echo "==> Starting Django shell..."
        exec python manage.py shell_plus 2>/dev/null || python manage.py shell
        ;;

    test)
        echo "==> Running tests..."
        exec pytest "${@:2}"
        ;;

    *)
        echo "==> Running custom command: $@"
        exec "$@"
        ;;
esac
