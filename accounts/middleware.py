import logging
import time

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    """
    Middleware layer — runs before every request reaches the view
    View has no idea this exists
    """

    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):
        # Before View runs
        start_time = time.time()

        logger.info(
            f"Incoming: {request.method} {request.path}"
        )

        # pass to next layer
        response = self.get_response(request)

        # After view runs
        duration = time.time() - start_time

        logger.info(
            f"Completed: {response.status_code} "
            f"in {duration:.3f}s"
        )

        return response