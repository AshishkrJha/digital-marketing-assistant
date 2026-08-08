from rest_framework import status
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses.
    """
    from rest_framework.views import exception_handler

    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            'error': True,
            'message': response.data.get('detail', 'An error occurred'),
            'data': response.data
        }

    return response
