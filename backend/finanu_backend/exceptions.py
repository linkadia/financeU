import math

from rest_framework import status
from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and isinstance(exc, Throttled):
        seconds_remaining = math.ceil(exc.wait or 0)
        response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
        response.data = {
            "error": "throttled",
            "message": "Request was throttled.",
            "seconds_remaining": seconds_remaining,
        }

    return response
