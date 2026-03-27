from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django Rest Framework to provide a consistent
    error response format.
    """
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now, customize the response data.
    if response is not None:
        custom_response = {
            'status_code': response.status_code,
            'error': {
                'type': exc.__class__.__name__,
                'detail': response.data.get('detail') if response.data.get('detail') else response.data
            },
            'message': 'An error occurred.'
        }
        
        if 'detail' in response.data:
            custom_response['message'] = response.data['detail']
        
        # Handle validation errors specifically
        if isinstance(response.data, dict) and not response.data.get('detail'):
            custom_response['error']['detail'] = response.data
            # Create a more descriptive message for validation errors
            error_messages = []
            for field, errors in response.data.items():
                error_messages.append(f"{field}: {' '.join(errors)}")
            custom_response['message'] = "Validation failed. " + " ".join(error_messages)


        response.data = custom_response

    return response
