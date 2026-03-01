"""
Celery tasks for user-related background operations.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, user_id: str):
    """Send a welcome email to a newly registered user."""
    try:
        user = User.objects.get(id=user_id)
        send_mail(
            subject="Welcome to Task Manager!",
            message=f"Hi {user.first_name},\n\n"
            f"Welcome to Task Manager! Your account has been created successfully.\n\n"
            f"Get started by creating your first project.\n\n"
            f"Best regards,\nThe Task Manager Team",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info("Welcome email sent to %s", user.email)
    except User.DoesNotExist:
        logger.warning("User %s not found for welcome email", user_id)
    except Exception as exc:
        logger.error("Failed to send welcome email to user %s: %s", user_id, exc)
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email(self, user_id: str, uid: str, token: str):
    """Send a password reset email with the reset link."""
    try:
        user = User.objects.get(id=user_id)
        # In production, construct the frontend URL
        reset_url = f"{settings.CORS_ALLOWED_ORIGINS[0]}/auth/reset-password?uid={uid}&token={token}"

        send_mail(
            subject="Password Reset Request",
            message=f"Hi {user.first_name},\n\n"
            f"You requested a password reset. Click the link below to reset your password:\n\n"
            f"{reset_url}\n\n"
            f"If you did not request this, please ignore this email.\n\n"
            f"This link will expire in 24 hours.\n\n"
            f"Best regards,\nThe Task Manager Team",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info("Password reset email sent to %s", user.email)
    except User.DoesNotExist:
        logger.warning("User %s not found for password reset email", user_id)
    except Exception as exc:
        logger.error("Failed to send password reset email to user %s: %s", user_id, exc)
        self.retry(exc=exc)


@shared_task
def cleanup_expired_tokens():
    """
    Clean up expired blacklisted tokens.
    Runs daily via Celery Beat.
    """
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )

    # Delete outstanding tokens older than the refresh token lifetime
    from django.utils import timezone
    from datetime import timedelta

    expiry_threshold = timezone.now() - settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]

    expired_count = OutstandingToken.objects.filter(
        expires_at__lt=expiry_threshold
    ).count()

    OutstandingToken.objects.filter(expires_at__lt=expiry_threshold).delete()

    logger.info("Cleaned up %d expired tokens", expired_count)
