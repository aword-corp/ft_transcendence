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
from .models import User, UserTwoFactorAuthData, Count, GroupChannel
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
        if user.blocked.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are blocked."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(
            {
                "user": {
                    "display_name": user.display_name,
                    "username": user.username,
                    "bio": user.bio,
                    "region": user.get_region_display(),
                    "country_code": user.country_code,
                    "language": user.get_language_display(),
                    "avatar_url": user.avatar_url.url if user.avatar_url else None,
                    "banner_url": user.banner_url.url if user.banner_url else None,
                    "grade": user.get_grade_display(),
                    "created_at": user.created_at,
                    "xp": int(user.xp),
                    "elo": int(user.elo),
                    "status": user.get_status_display(),
                    "is_friend": user.friends.filter(id=request.user.id).exists(),
                    "has_friend_request": request.user.friendrequests.filter(
                        id=user.id
                    ).exists(),
                    "sent_friend_request": user.friendrequests.filter(
                        id=request.user.id
                    ).exists(),
                    "has_dms": GroupChannel.objects.filter(
                        channel_type=GroupChannel.Type.DM
                    )
                    .filter(users=request.user)
                    .filter(users=user)
                    .distinct()
                    .exists(),
                    "is_blocked": request.user.blocked.filter(id=user.id).exists(),
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
@permission_classes([IsAuthenticated])
def SelfUserFriendsList(request):
    return Response(
        {"friends": [user.username for user in request.user.friends.all()]},
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def UserFriendsList(request, name: str):
    if name == request.user.username:
        return Response(
            {
                "friends": [
                    {
                        "name": user.username,
                        "avatar_url": user.avatar_url.url if user.avatar_url else None,
                        "display_name": user.display_name,
                        "grade": user.grade,
                        "verified": user.verified,
                    }
                    for user in request.user.friends.all()
                ]
            },
            status=status.HTTP_200_OK,
        )
    try:
        user = User.objects.get(username=name)
        if user.blocked.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are blocked."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if user.display_friends == user.Friend_Display.PRIVATE:
            return Response(
                {"error": "You cannot see this user friends list."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if (
            user.display_friends == user.Friend_Display.FRIENDS
            and not user.friends.filter(id=request.user.id).exists()
        ):
            return Response(
                {"error": "You cannot see this user friends list."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(
            {
                "friends": [
                    {
                        "name": user.username,
                        "avatar_url": user.avatar_url.url if user.avatar_url else None,
                        "display_name": user.display_name,
                        "grade": user.grade,
                        "verified": user.verified,
                    }
                    for user in user.friends.all()
                ]
            },
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([FivePerMinuteUserThrottle])
def UserFriendsAdd(request, name: str):
    if name == request.user.username:
        return Response(
            {"error": "You cannot add yourself."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user = User.objects.get(username=name)
        if user.blocked.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are blocked."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if user.friend_default_response == user.Friend_Request.REJECT:
            return Response(
                {"error": "You cannot send a friend request to this user."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if user.friends.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are already friend with this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.friend_default_response == user.Friend_Request.ACCEPT:
            user.friends.add(request.user)
            user.save()
            return Response(
                {"details": "ok."},
                status=status.HTTP_200_OK,
            )
        if user.friendrequests.filter(id=request.user.id).exists():
            return Response(
                {"error": "You already sent a friend request to this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.user.friendrequests.filter(id=user.id).exists():
            user.friends.add(request.user)
            request.user.friendrequests.remove(user)
            request.user.save()
        else:
            user.friendrequests.add(request.user)
        user.save()
        return Response(
            {"details": "ok."},
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([FivePerMinuteUserThrottle])
def UserFriendsRemove(request, name: str):
    if name == request.user.username:
        return Response(
            {"error": "You cannot remove yourself."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user = User.objects.get(username=name)
        if not user.friends.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are not friend with this user."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user.friends.remove(request.user)
        user.save()
        request.user.save()
        return Response(
            {"details": "ok."},
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([FivePerMinuteUserThrottle])
def UserFriendRequestAccept(request, name: str):
    if name == request.user.username:
        return Response(
            {"error": "You cannot accept yourself."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user = User.objects.get(username=name)
        if user.blocked.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are blocked."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not request.user.friendrequests.filter(id=user.id).exists():
            return Response(
                {"error": "You have no friend request from this user."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        request.user.friendrequests.remove(user)
        user.friends.add(request.user)
        user.save()
        request.user.save()
        return Response(
            {"details": "ok."},
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([FivePerMinuteUserThrottle])
def UserFriendRequestReject(request, name: str):
    if name == request.user.username:
        return Response(
            {"error": "You cannot reject yourself."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user = User.objects.get(username=name)
        if not request.user.friendrequests.filter(id=user.id).exists():
            return Response(
                {"error": "You have no friend request from this user."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        request.user.friendrequests.remove(user)
        request.user.save()
        return Response(
            {"details": "ok."},
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([FivePerMinuteUserThrottle])
def UserFriendRequestRemove(request, name: str):
    if name == request.user.username:
        return Response(
            {"error": "You cannot perform this action on yourself."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user = User.objects.get(username=name)
        if not user.friendrequests.filter(id=request.user.id).exists():
            return Response(
                {"error": "You have no pending request to this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.friendrequests.remove(request.user)
        user.save()
        return Response(
            {"details": "ok."},
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([FivePerMinuteUserThrottle])
def UserBlock(request, name: str):
    if name == request.user.username:
        return Response(
            {"error": "You cannot block yourself."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user = User.objects.get(username=name)
        if request.user.blocked.filter(id=user.id).exists():
            return Response(
                {"error": "You have already blocked this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.friends.filter(id=request.user.id).exists():
            user.friends.remove(request.user)
        if user.friendrequests.filter(id=request.user.id).exists():
            user.friendrequests.remove(request.user)
        if request.user.friendrequests.filter(id=user.id).exists():
            request.user.friendrequests.remove(user)
        request.user.blocked.add(user)
        user.save()
        request.user.save()
        return Response(
            {"details": "ok."},
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([FivePerMinuteUserThrottle])
def UserUnBlock(request, name: str):
    if name == request.user.username:
        return Response(
            {"error": "You cannot unblock yourself."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user = User.objects.get(username=name)
        if not request.user.blocked.filter(id=user.id).exists():
            return Response(
                {"error": "You did not block this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.blocked.remove(user)
        request.user.save()
        return Response(
            {"details": "ok."},
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def channel_username(request, name: str):
    if name == request.user.username:
        return Response(
            {"error": "You cannot start a private message channel with yourself."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user = User.objects.get(username=name)
        channel = (
            GroupChannel.objects.filter(channel_type=GroupChannel.Type.DM)
            .filter(users=request.user)
            .filter(users=user)
            .distinct()
            .first()
        )
        if not channel:
            if user.msg_default_response == User.Message_Request.BLOCK:
                return Response(
                    {
                        "error": "You cannot start a private message channel with this user."
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            channel = GroupChannel.objects.create()
            channel.users.add(user)
            channel.users.add(request.user)
        return Response({"channel_id": channel.id}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def channel_id(request, id: int):
    try:
        channel = GroupChannel.objects.get(id=id)
        if not channel.users.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are not allowed to see this channel."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(
            {
                "channel": {
                    "name": channel.name,
                    "description": channel.description,
                    "avatar_url": channel.avatar_url.url
                    if channel.avatar_url
                    else None,
                    "created_at": channel.created_at,
                    "channel_type": channel.channel_type,
                    "messages": [
                        {
                            "content": message.content,
                            "author": message.author.username,
                            "created_at": message.created_at,
                            "seen_by": [
                                user.username for user in message.seen_by.all()
                            ],
                            "edited": message.edited,
                        }
                        for message in channel.messages.all()
                    ],
                }
            },
            status=status.HTTP_200_OK,
        )

    except GroupChannel.DoesNotExist:
        return Response(
            {"error": "Channel not found."},
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
