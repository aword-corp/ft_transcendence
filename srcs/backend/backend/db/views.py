from .serializers import UserSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.permissions import BasePermission
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from django.contrib.auth import authenticate, login as django_login
from .models import User, UserTwoFactorAuthData
from .serializers import MyTokenObtainPairSerializer


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


@api_view(["POST"])
@permission_classes([IsNotAuthenticated])
def LoginView(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(request, username=username, password=password)

    if user is not None:
        user_profile = User.objects.get(user=user)

        if user_profile.has_2fa:
            return Response(
                {"detail": "Requires validation code."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        django_login(request, user)
        refresh = MyTokenObtainPairSerializer.for_user(user)
        access_token = str(refresh.access_token)

        return Response(
            {"access_token": access_token, "refresh_token": str(refresh)},
            status=status.HTTP_200_OK,
        )

    return Response(
        {"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(["POST"])
@permission_classes([IsNotAuthenticated])
def VerifyView(request):
    username = request.data.get("username")
    password = request.data.get("password")
    otp = request.data.get("otp")

    user = authenticate(request, username=username, password=password)

    if user is not None:
        user_profile = User.objects.get(user=user)
        if user_profile.has_2fa:
            two_factor_auth_data = UserTwoFactorAuthData.objects.filter(
                user=user
            ).first()

            otp = "".join(filter(str.isdigit, otp))

            if not two_factor_auth_data.validate_otp(otp):
                return Response(
                    {"detail": "Invalid verification code or credentials."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        django_login(request, user)
        refresh = MyTokenObtainPairSerializer.for_user(user)
        access_token = str(refresh.access_token)

        return Response(
            {"access_token": access_token, "refresh_token": str(refresh)},
            status=status.HTTP_200_OK,
        )
