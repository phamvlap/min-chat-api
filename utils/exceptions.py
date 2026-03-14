from typing import Any

from rest_framework.exceptions import ErrorDetail


def extract_serializer_error(error: Any) -> tuple[str, str]:
    if isinstance(error, ErrorDetail):
        return str(error.code), str(error)

    if isinstance(error, (list, tuple)) and error:
        for err in error:
            code, message = extract_serializer_error(err)
            if message:
                return code, message

    if isinstance(error, dict):
        for _, value in error.items():
            code, message = extract_serializer_error(value)
            if message:
                return code, message

    return "unknown_error", "An unknown error occurred."
