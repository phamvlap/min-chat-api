import logging
import time
import uuid
from contextvars import ContextVar

logger = logging.getLogger("api.request")

correlation_id_var = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str | None:
    return correlation_id_var.get()


def set_correlation_id(correlation_id) -> None:
    correlation_id_var.set(correlation_id)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)

        duration = (time.time() - start_time) * 1000  # Convert to milliseconds

        logger.info(
            f"{request.method} {request.path} | status={response.status_code} | duration={duration:.2f}ms"
        )

        return response


class RequestTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()

        response = self.get_response(request)

        duration = (time.perf_counter() - start_time) * 1000  # Convert to milliseconds

        response["X-Response-Time-ms"] = f"{duration:.2f}"

        # Log the slow requests
        if duration > 800:  # Log requests that take longer than 800 ms
            logger.warning(
                f"[SLOW REQUEST]: {request.method} {request.path} | status={response.status_code} | duration={duration:.2f}ms"
            )

        return response


class CorrelationIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # Set the correlation ID in the context variable for access in views and other parts of the code
        set_correlation_id(correlation_id)

        # Attach the correlation ID to the request object for access in views
        request.correlation_id = correlation_id

        response = self.get_response(request)

        # Add the correlation ID to the response headers for client-side tracking
        response["X-Correlation-ID"] = correlation_id

        return response
