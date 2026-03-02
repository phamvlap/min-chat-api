import logging
import time

logger = logging.getLogger("api.request")


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
