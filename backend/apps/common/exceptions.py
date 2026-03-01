"""
Custom exception handling for DRF.
"""

import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


# ── Domain Exceptions (used by managers to signal business-logic errors) ──────

class NotFoundError(APIException):
    """Raised when a requested resource does not exist."""
    status_code = 404
    default_code = "not_found"
    default_detail = "The requested resource was not found."


class ConflictError(APIException):
    """Raised when an operation conflicts with existing state (e.g. duplicate)."""
    status_code = 409
    default_code = "conflict"
    default_detail = "A conflict occurred with the current state of the resource."


class ForbiddenError(APIException):
    """Raised when a user is authenticated but lacks permission."""
    status_code = 403
    default_code = "forbidden"
    default_detail = "You do not have permission to perform this action."


class BusinessRuleError(APIException):
    """Raised when a business rule is violated (e.g. last owner cannot be removed)."""
    status_code = 400
    default_code = "business_rule_violation"
    default_detail = "This action violates a business rule."


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error response format.

    Response format:
    {
        "error": {
            "code": "error_code",
            "message": "Human-readable message",
            "details": {} or []
        }
    }
    """
    # Convert Django ValidationError to DRF ValidationError
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

    # Call DRF's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            "error": {
                "code": _get_error_code(exc),
                "message": _get_error_message(exc, response),
                "details": _get_error_details(exc, response),
            }
        }
        response.data = error_payload
    else:
        # Unhandled exceptions — log and return 500
        logger.exception(
            "Unhandled exception in %s",
            context.get("view", "unknown"),
            exc_info=exc,
        )
        response = Response(
            {
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "details": {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _get_error_code(exc) -> str:
    """Derive an error code string from the exception type."""
    if isinstance(exc, ValidationError):
        return "validation_error"
    if isinstance(exc, Http404):
        return "not_found"
    if isinstance(exc, APIException):
        return exc.default_code if hasattr(exc, "default_code") else "api_error"
    return "internal_server_error"


def _get_error_message(exc, response) -> str:
    """Derive a human-readable error message."""
    if isinstance(exc, ValidationError):
        return "Validation failed. Check the details for specific field errors."
    if isinstance(exc, Http404):
        return "The requested resource was not found."
    if hasattr(exc, "detail"):
        detail = exc.detail
        if isinstance(detail, str):
            return detail
        if isinstance(detail, list) and len(detail) > 0:
            return str(detail[0])
    return "An error occurred."


def _get_error_details(exc, response):
    """Extract detailed error information."""
    if isinstance(exc, ValidationError):
        return response.data if response else {}
    return {}
