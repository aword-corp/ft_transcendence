from .serializers import UserSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.permissions import BasePermission
from rest_framework.throttling import UserRateThrottle


class FivePerMinuteUserThrottle(UserRateThrottle):
    rate = "5/min"


class IsNotAuthenticated(BasePermission):
    """
    Allows access only to unauthenticated users.
    """

    def has_permission(self, request, view):
        return bool(not request.user or not request.user.is_authenticated)


@api_view(["POST"])
@permission_classes([IsNotAuthenticated])
@throttle_classes([FivePerMinuteUserThrottle])
def RegisterView(request):
    serializer = UserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
