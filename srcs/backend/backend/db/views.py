from .serializers import UserSerializer, MyTokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.permissions import BasePermission
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from django.contrib.auth import authenticate, login as django_login
from .models import User, UserTwoFactorAuthData
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
import pyotp


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
        user_profile = User.objects.get(id=user.id)

        if user_profile.has_2fa:
            return Response(
                {"detail": "Requires validation code."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        django_login(request, user)
        refresh = MyTokenObtainPairSerializer.get_token(user)
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
        user_profile = User.objects.get(id=user.id)
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
        refresh = MyTokenObtainPairSerializer.get_token(user)
        access_token = str(refresh.access_token)

        return Response(
            {"access_token": access_token, "refresh_token": str(refresh)},
            status=status.HTTP_200_OK,
        )


def user_two_factor_auth_data_create(*, user: User) -> UserTwoFactorAuthData:
    if user.has_2fa:
        raise ValidationError("Can not have more than one 2FA related data.")

    two_factor_auth_data = UserTwoFactorAuthData.objects.create(
        user=user, otp_secret=pyotp.random_base32()
    )
    user.has_2fa = True
    user.save()
    two_factor_auth_data.save()
    return two_factor_auth_data


class TenPerDayUserThrottle(UserRateThrottle):
    rate = "10/day"


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([TenPerDayUserThrottle])
def setup_2fa(request):
    user = request.user

    try:
        two_factor_auth_data = user_two_factor_auth_data_create(user=user)

        otp_secret = two_factor_auth_data.otp_secret
        qr_code = two_factor_auth_data.generate_qr_code(name=user.email)

        return Response(
            {"otp_secret": otp_secret, "qr_code": qr_code},
            status=status.HTTP_200_OK,
        )
    except ValidationError as exc:
        message = exc.messages
    return Response(
        {"details": message},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([TenPerDayUserThrottle])
def remove_2fa(request):
    try:
        user = User.objects.get(id=request.user.id)

        if user and user.has_2fa:
            UserTwoFactorAuthData.objects.filter(user=user).delete()
            user.has_2fa = False
            user.save()
            return Response(
                {"detail": "Successfully removed two factor authentication."},
                status=status.HTTP_200_OK,
            )

    except User.DoesNotExist:
        pass

    return Response(
        {"detail": "Invalid credentials or user has not two factor enabled."},
        status=status.HTTP_401_UNAUTHORIZED,
    )
