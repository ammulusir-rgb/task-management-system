"""
Celery application configuration for Task Management SaaS.
"""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("taskmanager")

# Load config from Django settings, using the CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# ── Periodic Tasks (Celery Beat) ──
app.conf.beat_schedule = {
    "send-due-date-reminders": {
        "task": "apps.tasks.tasks.send_due_date_reminders",
        "schedule": crontab(hour=8, minute=0),  # Every day at 8 AM UTC
    },
    "send-overdue-notifications": {
        "task": "apps.tasks.tasks.send_overdue_notifications",
        "schedule": crontab(hour=9, minute=0),  # Every day at 9 AM UTC
    },
    "process-incoming-emails": {
        "task": "apps.emails.tasks.process_incoming_emails",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    "generate-daily-report-snapshot": {
        "task": "apps.reports.tasks.generate_daily_report_snapshot",
        "schedule": crontab(hour=0, minute=30),  # Every day at 00:30 UTC
    },
    "cleanup-expired-tokens": {
        "task": "apps.users.tasks.cleanup_expired_tokens",
        "schedule": crontab(hour=2, minute=0),  # Every day at 2 AM UTC
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f"Request: {self.request!r}")
