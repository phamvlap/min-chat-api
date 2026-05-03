from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    ErrorDetail,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler

from base.exceptions import BaseAPIException


def get_error_detail(error_data: dict[str, Any]) -> dict[str, Any]:
    error_details = {}

    for key, value in error_data.items():
        if value and isinstance(value, list) and isinstance(value[0], ErrorDetail):
            error_details[key] = {
                "code": value[0].code,
                "message": str(value[0]),
            }
        elif isinstance(value, dict):
            error_details[key] = get_error_detail(value)
        else:
            error_details[key] = value

    return error_details


def custom_exception_handler(exc, context):
    NON_FIELD_ERRORS_KEY = "non_field_errors"

    # Convert Django's ValidationError to DRF's ValidationError to ensure consistent error handling
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(as_serializer_error(exc))

    if isinstance(exc, Http404):
        exc = NotFound(str(exc))

    if isinstance(exc, DjangoPermissionDenied):
        exc = PermissionDenied(str(exc))

    # Call REST framework's default exception handler first to get the standard error response
    response = exception_handler(exc, context)

    if isinstance(exc, BaseAPIException):
        response.data = {
            "code": exc.default_code,
            "message": exc.detail,
        }
        return response

    # Unexpected error (500 Internal Server Error) will result in response being None, so we need to handle that case as well.
    if response is None:
        return Response(
            {
                "code": "internal_server_error",
                "message": "Something went wrong. Please try again later.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Handle the case when the exception has a 'detail' attribute that is an instance of ErrorDetail
    if "detail" in response.data and isinstance(response.data["detail"], ErrorDetail):
        response.data = {
            "code": response.data["detail"].code,
            "message": str(response.data["detail"]),
        }
        return response

    # Handle the case when the exception has a 'code' attribute in the response data
    if "code" in response.data:

        def _get_error_code(exc) -> str | None:
            if isinstance(exc, Throttled):
                return "throttled"

            if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
                return "authentication_failed"

            if isinstance(exc, PermissionDenied):
                return "permission_denied"

            return None

        def _get_error_message(response: Response) -> str:
            error_message = "Unknown error occurred."

            if "message" in response.data and isinstance(response.data["message"], (str, list)):
                error_message = (
                    str(response.data["message"][0])
                    if isinstance(response.data["message"], list)
                    else response.data["message"]
                )

            return error_message

        response.data = {
            "code": _get_error_code(exc) or response.data["code"],
            "message": _get_error_message(response),
        }
        return response

    # Handle validation errors and other errors without a specific code
    if isinstance(exc, ValidationError):
        # If there are non_field_errors, use the first one as the main error message and code
        if NON_FIELD_ERRORS_KEY in response.data and isinstance(
            response.data[NON_FIELD_ERRORS_KEY],
            list,
        ):
            error_detail = response.data[NON_FIELD_ERRORS_KEY][0]

            response.data = {
                "code": error_detail.code,
                "message": str(error_detail),
            }
            return response

        # For nested/complex validation errors, we can use the get_error_detail function to extract the details and return a structured response
        response.data = {
            "code": "validation_error",
            "message": "Validation failed. Please check the input data.",
            "detail": get_error_detail(response.data),
        }
        return response

    # Fallback for any other errors that don't fit the above cases, ensuring we always return a consistent error response format
    response.data = {
        "code": "unknown_error",
        "message": "An unknown error occurred. Please try again later.",
        "detail": get_error_detail(response.data),
    }

    return response
