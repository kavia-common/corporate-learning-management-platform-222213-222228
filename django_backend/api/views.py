from rest_framework.decorators import api_view
from rest_framework.response import Response

# PUBLIC_INTERFACE
@api_view(["GET"])
def health(request):
    """
    Health check endpoint.

    Summary:
    - Returns server readiness status.

    Returns:
      200 OK with {"message": "Server is up!"}
    """
    return Response({"message": "Server is up!"})
