"""
Business-logic manager for Email Configurations, Rules, and Processed Emails.
Views delegate to this class; all methods carry enter/exit/error logging
and raise domain exceptions on failure.
"""

import logging

from django.shortcuts import get_object_or_404

from apps.common.exceptions import BusinessRuleError, ForbiddenError
from apps.organizations.models import Organization

from .models import EmailConfiguration, EmailRule, ProcessedEmail

logger = logging.getLogger(__name__)


class EmailManager:
    """Handles all business logic for the emails app."""

    # ── Access helpers ────────────────────────────────────────────────────────

    def _assert_org_member(self, organization, user) -> None:
        """Raise ForbiddenError if *user* is not a member of *organization*."""
        if not organization.members.filter(id=user.id).exists():
            raise ForbiddenError("You do not have access to this organization.")

    # ── Email Configuration ───────────────────────────────────────────────────

    def get_configurations(self, user, org_id: str):
        """
        Return email configurations for *org_id*.
        Returns an empty queryset if *user* is not a member.
        """
        logger.debug("ENTER EmailManager.get_configurations | user=%s org=%s", user.pk, org_id)
        try:
            if not org_id:
                logger.debug("EXIT EmailManager.get_configurations | no org_id -> empty")
                return EmailConfiguration.objects.none()
            organization = get_object_or_404(Organization, id=org_id)
            if not organization.members.filter(id=user.id).exists():
                logger.debug("EXIT EmailManager.get_configurations | user=%s not member -> empty", user.pk)
                return EmailConfiguration.objects.none()
            qs = EmailConfiguration.objects.filter(organization=organization)
            logger.debug("EXIT EmailManager.get_configurations | org=%s count=%d", org_id, qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR EmailManager.get_configurations: %s", exc, exc_info=True)
            raise

    def create_configuration(self, serializer, user, org_id: str) -> EmailConfiguration:
        """Create an email configuration for *org_id*. Raises ForbiddenError."""
        logger.debug("ENTER EmailManager.create_configuration | user=%s org=%s", user.pk, org_id)
        try:
            organization = get_object_or_404(Organization, id=org_id)
            self._assert_org_member(organization, user)
            config = serializer.save(organization=organization)
            logger.debug("EXIT EmailManager.create_configuration | config=%s", config.pk)
            return config
        except ForbiddenError:
            raise
        except Exception as exc:
            logger.error("ERROR EmailManager.create_configuration: %s", exc, exc_info=True)
            raise

    def test_connection(self, config, test_task) -> str:
        """Dispatch async connection-test task. Returns Celery task id."""
        logger.debug("ENTER EmailManager.test_connection | config=%s", config.pk)
        try:
            task = test_task.delay(str(config.id))
            logger.debug("EXIT EmailManager.test_connection | config=%s task=%s", config.pk, task.id)
            return task.id
        except Exception as exc:
            logger.error("ERROR EmailManager.test_connection: %s", exc, exc_info=True)
            raise

    def process_emails(self, config, process_task) -> str:
        """
        Dispatch async email-processing task.
        Raises BusinessRuleError if IMAP is not enabled.
        Returns Celery task id.
        """
        logger.debug("ENTER EmailManager.process_emails | config=%s", config.pk)
        try:
            if not config.imap_enabled:
                raise BusinessRuleError("IMAP is not enabled for this configuration.")
            task = process_task.delay(str(config.organization.id))
            logger.debug("EXIT EmailManager.process_emails | config=%s task=%s", config.pk, task.id)
            return task.id
        except BusinessRuleError:
            raise
        except Exception as exc:
            logger.error("ERROR EmailManager.process_emails: %s", exc, exc_info=True)
            raise

    # ── Email Rules ───────────────────────────────────────────────────────────

    def get_rules(self, user, org_id: str):
        """
        Return email rules for *org_id*.
        Returns an empty queryset if *user* is not a member.
        """
        logger.debug("ENTER EmailManager.get_rules | user=%s org=%s", user.pk, org_id)
        try:
            if not org_id:
                logger.debug("EXIT EmailManager.get_rules | no org_id -> empty")
                return EmailRule.objects.none()
            organization = get_object_or_404(Organization, id=org_id)
            if not organization.members.filter(id=user.id).exists():
                logger.debug("EXIT EmailManager.get_rules | user=%s not member -> empty", user.pk)
                return EmailRule.objects.none()
            qs = EmailRule.objects.filter(organization=organization)
            logger.debug("EXIT EmailManager.get_rules | org=%s count=%d", org_id, qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR EmailManager.get_rules: %s", exc, exc_info=True)
            raise

    def create_rule(self, serializer, user, org_id: str) -> EmailRule:
        """Create an email rule for *org_id*. Raises ForbiddenError."""
        logger.debug("ENTER EmailManager.create_rule | user=%s org=%s", user.pk, org_id)
        try:
            organization = get_object_or_404(Organization, id=org_id)
            self._assert_org_member(organization, user)
            rule = serializer.save(organization=organization)
            logger.debug("EXIT EmailManager.create_rule | rule=%s", rule.pk)
            return rule
        except ForbiddenError:
            raise
        except Exception as exc:
            logger.error("ERROR EmailManager.create_rule: %s", exc, exc_info=True)
            raise

    # ── Processed Emails ──────────────────────────────────────────────────────

    def get_processed_emails(self, user, org_id: str):
        """
        Return processed emails for *org_id*.
        Returns an empty queryset if *user* is not a member.
        """
        logger.debug("ENTER EmailManager.get_processed_emails | user=%s org=%s", user.pk, org_id)
        try:
            if not org_id:
                logger.debug("EXIT EmailManager.get_processed_emails | no org_id -> empty")
                return ProcessedEmail.objects.none()
            organization = get_object_or_404(Organization, id=org_id)
            if not organization.members.filter(id=user.id).exists():
                logger.debug("EXIT EmailManager.get_processed_emails | user=%s not member -> empty", user.pk)
                return ProcessedEmail.objects.none()
            qs = ProcessedEmail.objects.filter(organization=organization)
            logger.debug("EXIT EmailManager.get_processed_emails | org=%s count=%d", org_id, qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR EmailManager.get_processed_emails: %s", exc, exc_info=True)
            raise


# Module-level singleton
email_manager = EmailManager()
