"""
Custom User Manager for email-based authentication.
Also contains UserBusinessManager for view-layer business logic.
"""

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.common.exceptions import BusinessRuleError, NotFoundError

logger = logging.getLogger(__name__)


class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    for authentication instead of usernames.
    """

    def create_user(self, email: str, password: str = None, **extra_fields):
        """Create and return a regular user with the given email and password."""
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str = None, **extra_fields):
        """Create and return a superuser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "ADMIN")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class UserBusinessManager:
    """
    Business-logic layer for user management.
    All public methods follow the pattern:
        ENTER log → try/except → EXIT log (or ERROR log).
    Views delegate to this class; it raises domain exceptions on failure.
    """

    # Singleton-style: views import and instantiate once
    def __init__(self):
        self._User = None  # lazy-loaded

    @property
    def User(self):
        if self._User is None:
            self._User = get_user_model()
        return self._User

    # ── Query helpers ─────────────────────────────────────────────────────────

    def get_user_queryset(self, search: str = None, role: str = None, is_active: str = None):
        """Return a filtered queryset of all users for admin management."""
        logger.debug("ENTER UserBusinessManager.get_user_queryset | search=%s role=%s is_active=%s",
                     search, role, is_active)
        try:
            qs = self.User.objects.all().order_by("-date_joined")
            if search:
                qs = qs.filter(
                    Q(email__icontains=search)
                    | Q(first_name__icontains=search)
                    | Q(last_name__icontains=search)
                )
            if role:
                qs = qs.filter(role=role)
            if is_active is not None:
                qs = qs.filter(is_active=is_active.lower() == "true")
            logger.debug("EXIT UserBusinessManager.get_user_queryset -> count=%d", qs.count())
            return qs
        except Exception as exc:
            logger.error("ERROR UserBusinessManager.get_user_queryset: %s", exc, exc_info=True)
            raise

    # ── Password management ───────────────────────────────────────────────────

    def change_password(self, user, old_password: str, new_password: str) -> None:
        """Verify old password and set a new one. Raises BusinessRuleError if wrong."""
        logger.debug("ENTER UserBusinessManager.change_password | user=%s", user.pk)
        try:
            if not user.check_password(old_password):
                raise BusinessRuleError("Current password is incorrect.")
            user.set_password(new_password)
            user.save(update_fields=["password"])
            logger.debug("EXIT UserBusinessManager.change_password | user=%s password changed", user.pk)
        except BusinessRuleError:
            logger.warning("WARN UserBusinessManager.change_password | invalid old_password for user=%s", user.pk)
            raise
        except Exception as exc:
            logger.error("ERROR UserBusinessManager.change_password: %s", exc, exc_info=True)
            raise

    def request_password_reset(self, email: str, send_task) -> None:
        """
        Look up user by email and dispatch a reset email task.
        Silently succeeds even if email is unknown (security best practice).
        """
        logger.debug("ENTER UserBusinessManager.request_password_reset | email=%s", email)
        try:
            try:
                user = self.User.objects.get(email=email, is_active=True)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                send_task.delay(user.id, uid, token)
                logger.debug("EXIT UserBusinessManager.request_password_reset | email=%s reset dispatched", email)
            except self.User.DoesNotExist:
                logger.debug("EXIT UserBusinessManager.request_password_reset | email=%s not found (silent)", email)
        except Exception as exc:
            logger.error("ERROR UserBusinessManager.request_password_reset: %s", exc, exc_info=True)
            raise

    # ── Soft-delete ───────────────────────────────────────────────────────────

    def deactivate_user(self, user) -> None:
        """Soft-deactivate a user account."""
        logger.debug("ENTER UserBusinessManager.deactivate_user | user=%s", user.pk)
        try:
            user.is_active = False
            user.save(update_fields=["is_active"])
            logger.debug("EXIT UserBusinessManager.deactivate_user | user=%s deactivated", user.pk)
        except Exception as exc:
            logger.error("ERROR UserBusinessManager.deactivate_user: %s", exc, exc_info=True)
            raise


# Module-level singleton used by views
user_manager = UserBusinessManager()
