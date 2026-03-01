"""
Celery tasks for report generation.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def generate_daily_report_snapshot():
    """
    Generate and cache daily report snapshots for all active projects.
    Runs at 00:30 UTC via Celery Beat.
    """
    from django.core.cache import cache

    from apps.projects.models import Project
    from apps.reports.services import ReportService

    active_projects = Project.objects.filter(
        status="ACTIVE",
        deleted_at__isnull=True,
    )

    generated = 0
    for project in active_projects:
        try:
            service = ReportService(project)
            summary = service.get_project_summary()
            cache_key = f"report_snapshot:{project.id}"
            cache.set(cache_key, summary, timeout=60 * 60 * 25)  # 25 hours
            generated += 1
        except Exception as exc:
            logger.error(
                "Failed to generate report snapshot for project %s: %s",
                project.id,
                exc,
            )

    logger.info("Generated %d daily report snapshots", generated)
    return generated
