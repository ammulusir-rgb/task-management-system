"""
Organization signals.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Organization

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Organization)
def organization_post_save(sender, instance, created, **kwargs):
    if created:
        logger.info("Organization created: %s (slug=%s)", instance.name, instance.slug)
