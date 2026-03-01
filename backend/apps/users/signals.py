"""
User signals — post-save hooks.
"""

import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

User = get_user_model()


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """
    Post-save signal for User model.
    - Log new user registrations
    - Auto-create a personal organization for the new user
    """
    if created:
        logger.info("New user registered: %s (role=%s)", instance.email, instance.role)
        _create_personal_organization(instance)


def _create_personal_organization(user):
    """Create a default personal organization for a newly registered user."""
    from apps.organizations.models import Organization, OrganizationMember, OrganizationRole

    try:
        org_name = f"{user.first_name or user.email.split('@')[0]}'s Organization"
        org = Organization(name=org_name, created_by=user)
        org.save()  # save() auto-generates the slug

        OrganizationMember.objects.create(
            organization=org,
            user=user,
            role=OrganizationRole.OWNER,
        )
        logger.info("Created personal organization '%s' for user %s", org.name, user.email)
    except Exception as exc:
        logger.error("Failed to create personal org for user %s: %s", user.email, exc)
