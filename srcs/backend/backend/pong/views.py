from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def MatchmakingView(request):
    return Response({"detail": "Nothing."}, status=status.HTTP_501_NOT_IMPLEMENTED)
