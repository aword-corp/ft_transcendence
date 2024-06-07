from .serializers import UserSerializer, MyTokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework.decorators import (
    api_view,
    throttle_classes,
    permission_classes,
)
from rest_framework.request import Request
from rest_framework.permissions import BasePermission
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from django.contrib.auth import authenticate, login as django_login
from .models import User, UserTwoFactorAuthData, Count
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
import pyotp
from time import time_ns
from operator import itemgetter
from datetime import timedelta
import json
import requests
from django.conf import settings


class time_cache:
    def __init__(self, time=1):
        self.time = time.total_seconds() if isinstance(time, timedelta) else time
        self.cache = {}

    def __call__(self, fun):
        def wrapped(*args):
            now = time_ns() // 1e9
            if fun not in self.cache or now > self.cache[fun]["next_call"]:
                self.cache[fun] = {
                    "last_result": fun(*args),
                    "next_call": now + self.time,
                }
            else:
                print(f"{fun.__name__} call, using last result")
            return self.cache[fun]["last_result"]

        return wrapped


class FivePerMinuteUserThrottle(UserRateThrottle):
    rate = "5/min"


class IsNotAuthenticated(BasePermission):
    """
    Allows access only to unauthenticated users.
    """

    def has_permission(self, request, view):
        return bool(not request.user or not request.user.is_authenticated)


@api_view(["GET"])
def HomeView(request):
    return Response(
        {"details": "ok."},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsNotAuthenticated])
@throttle_classes([FivePerMinuteUserThrottle])
def RegisterView(request):
    serializer = UserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ValidateView(request):
    return Response({"detail": "Ok."}, status=status.HTTP_200_OK)


# class ft_callback(views.APIView):
#     required_param_fields = ["code"]

#     def get(self, request: Request, *args, **kwargs):


@api_view(["GET"])
@permission_classes([IsNotAuthenticated])
def ft_callback(request: Request):
    code = request.GET.get("code")
    if not code:
        return Response(
            {"detail": "No code provided."}, status=status.HTTP_400_BAD_REQUEST
        )
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.FT_API_UID,
        "client_secret": settings.FT_API_SECRET,
        "code": code,
        "redirect_uri": settings.FT_REDIRECT,
    }
    post = requests.post("https://api.intra.42.fr/oauth/token", json=data)
    post_json = post.json()
    if "access_token" not in post_json:
        return Response(
            {"detail": "Could not authenticate."}, status=status.HTTP_401_UNAUTHORIZED
        )
    headers = {"Authorization": f'Bearer {post_json["access_token"]}'}
    me = requests.get("https://api.intra.42.fr/v2/me", headers=headers)
    me_json = me.json()
    email = me_json["email"]
    try:
        user = User.objects.get(email=email)
        if not user.has_ft:
            return Response(
                {"detail": "Could not authenticate."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        django_login(request, user, backend="db.authentication.FTAuthBackend")
        refresh = MyTokenObtainPairSerializer.get_token(user)
        access_token = str(refresh.access_token)
        return Response(
            {"access_token": access_token, "refresh_token": str(refresh)},
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        user = User.objects.create(
            email=email,
            username=me_json["login"],
            region="eu-we",
            country_code="FR",
            language="FR-FR",
            has_ft=True,
        )
        user.set_unusable_password()
        user.save()
        django_login(request, user, backend="db.authentication.FTAuthBackend")
        refresh = MyTokenObtainPairSerializer.get_token(user)
        access_token = str(refresh.access_token)
        return Response(
            {"access_token": access_token, "refresh_token": str(refresh)},
            status=status.HTTP_200_OK,
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


@api_view(["GET"])
def get_clicks(request):
    counter, created = Count.objects.get_or_create(id=1)
    if created:
        counter.save()
    return Response(
        {"count": counter.clicks},
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def UserProfileView(request, name: str):
    try:
        user = User.objects.get(username=name)
        return Response(
            {
                "user": {
                    "display_name": user.display_name,
                    "username": user.username,
                    "bio": user.bio,
                    "region": user.get_region_display(),
                    "country_code": user.country_code,
                    "language": user.get_language_display(),
                    "avatar_url": user.avatar_url if user.avatar_url else None,
                    "banner_url": user.banner_url if user.banner_url else None,
                    "grade": user.get_grade_display(),
                    "created_at": user.created_at,
                    "xp": int(user.xp),
                    "elo": int(user.elo),
                    "status": user.get_status_display(),
                }
            },
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["GET"])
@time_cache(time=timedelta(seconds=10))
def get_leaderboard(request) -> Response:
    print("---------Get leaderboard call---------")
    leaderboard = sorted(User.objects.values(), key=itemgetter("elo"))
    print(leaderboard)

    return Response(
        {
            "leaderboard": json.dumps(
                {name["username"]: name["elo"] for name in leaderboard}
            )
        },
        status=status.HTTP_200_OK,
    )
