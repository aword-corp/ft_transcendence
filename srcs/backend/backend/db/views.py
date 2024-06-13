import uuid
from .serializers import EditUserSerializer, UserSerializer, MyTokenObtainPairSerializer
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
from .models import Game, User, UserTwoFactorAuthData, Count, GroupChannel, Messages
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
import pyotp
from time import time_ns
from operator import itemgetter
from datetime import timedelta
import json
import requests
from django.conf import settings
from django.core.cache import cache
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.generics import UpdateAPIView


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


@api_view(
    ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "CONNECT", "TRACE"]
)
def error_400_view(request, exception):
    return Response(
        {"error": "Bad request."},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(
    ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "CONNECT", "TRACE"]
)
def error_403_view(request, exception):
    return Response(
        {"error": "Forbidden."},
        status=status.HTTP_403_FORBIDDEN,
    )


@api_view(
    ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "CONNECT", "TRACE"]
)
def error_404_view(request, exception):
    return Response(
        {"error": "Not found."},
        status=status.HTTP_404_NOT_FOUND,
    )


@api_view(
    ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "CONNECT", "TRACE"]
)
def error_500_view(request):
    return Response(
        {"error": "Internal server error."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@api_view(["POST"])
@permission_classes([IsNotAuthenticated])
@throttle_classes([FivePerMinuteUserThrottle])
def RegisterView(request):
    serializer = UserSerializer(data=request.data)
    try:
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except KeyError:
        return Response(
            {"error": "Missing required field."},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([FivePerMinuteUserThrottle])
def EditProfileView(request):
    try:
        user = User.objects.get(id=request.user.id)
        serializer = EditUserSerializer(data=request.data, instance=user, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        channel_layer = get_channel_layer()

        channels = cache.get(f"user_{request.user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "profile.update.sent",
                        "from": request.user.username,
                    },
                )

        for user in user.friends.all():
            channels = cache.get(f"user_{user.id}_channel")

            if channels:
                for channel in channels:
                    async_to_sync(channel_layer.send)(
                        channel,
                        {
                            "type": "profile.update.received",
                            "from": request.user.username,
                        },
                    )

        return Response(serializer.data, status=status.HTTP_200_OK)
    except KeyError:
        return Response(
            {"error": "Missing required field."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
@permission_classes([IsNotAuthenticated])
def LoginView(request):
    username = request.data.get("username")

    if not username:
        return Response(
            {"detail": "No email or username provided."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    password = request.data.get("password")

    if not password:
        return Response(
            {"detail": "No password provided."},
            status=status.HTTP_400_BAD_REQUEST,
        )

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
        django_login(request, user, backend="db.authentication.CustomAuthBackend")
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
        django_login(request, user, backend="db.authentication.CustomAuthBackend")
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
        player_games = Game.objects.filter(
            users=user, game_type=Game.Type.MM, state=Game.State.ENDED
        ).all()
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
                    "elo_history": [
                        {"elo": int(elo.elo), "date": elo.date}
                        for elo in user.elo_history.all()
                    ],
                    "is_online": user.is_online and not user.is_invisible,
                    "is_focused": user.is_focused and not user.is_invisible,
                    "is_spectating": user.is_spectating and not user.is_invisible,
                    "is_playing": user.is_playing and not user.is_invisible,
                    "is_friend": user.friends.filter(id=request.user.id).exists(),
                    "has_friend_request": request.user.id != user.id
                    and request.user.friendrequests.filter(id=user.id).exists(),
                    "sent_friend_request": request.user.id != user.id
                    and user.friendrequests.filter(id=request.user.id).exists(),
                    "has_dms": request.user.id != user.id
                    and GroupChannel.objects.filter(channel_type=GroupChannel.Type.DM)
                    .filter(users=request.user)
                    .filter(users=user)
                    .distinct()
                    .exists(),
                    "can_dm": request.user.id != user.id
                    and (
                        user.msg_default_response != User.Message_Request.BLOCK
                        or user.friends.filter(id=request.user.id).exists()
                        or GroupChannel.objects.filter(
                            channel_type=GroupChannel.Type.DM
                        )
                        .filter(users=request.user)
                        .filter(users=user)
                        .distinct()
                        .exists()
                    )
                    and not request.user.blocked.filter(id=user.id).exists(),
                    "is_blocked": request.user.id != user.id
                    and request.user.blocked.filter(id=user.id).exists(),
                    "wins": player_games.filter(winner=user).count(),
                    "losses": player_games.filter(loser=user).count(),
                    "game_count": player_games.count(),
                    "games": [
                        {
                            "uuid": game.uuid,
                            "date": game.date,
                            "winner": {
                                "username": game.winner.username,
                                "display_name": game.winner.display_name,
                                "elo": game.elo_winner,
                                "avatar_url": game.winner.avatar_url.url
                                if game.winner.avatar_url
                                else None,
                            },
                            "loser": {
                                "username": game.loser.username,
                                "display_name": game.loser.display_name,
                                "elo": game.elo_loser,
                                "avatar_url": game.loser.avatar_url.url
                                if game.loser.avatar_url
                                else None,
                            },
                            "score_winner": game.score_winner,
                            "score_loser": game.score_loser,
                        }
                        for game in player_games
                    ],
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
    try:
        user = User.objects.get(id=request.user.id)
        return Response(
            {
                "friends": [
                    {
                        "name": friend.username,
                        "avatar_url": friend.avatar_url.url
                        if friend.avatar_url
                        else None,
                        "display_name": friend.display_name,
                        "grade": friend.grade,
                        "verified": friend.verified,
                    }
                    for friend in user.friends.all()
                ]
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
def UserFriendsList(request, name: str):
    try:
        user = User.objects.get(username=name)
        if user.blocked.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are blocked."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if (
            request.user.id != user.id
            and user.display_friends == user.Friend_Display.PRIVATE
        ):
            return Response(
                {"error": "You cannot see this user friends list."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if (
            request.user.id != user.id
            and user.display_friends == user.Friend_Display.FRIENDS
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
                        "name": friend.username,
                        "avatar_url": friend.avatar_url.url
                        if friend.avatar_url
                        else None,
                        "display_name": friend.display_name,
                        "grade": friend.grade,
                        "verified": friend.verified,
                    }
                    for friend in user.friends.all()
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
def UserFriendsAdd(request, name: str):
    try:
        user = User.objects.get(username=name)
        if user.id == request.user.id:
            return Response(
                {"error": "You cannot add yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )
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
        if user.friendrequests.filter(id=request.user.id).exists():
            return Response(
                {"error": "You already sent a friend request to this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.friend_default_response == user.Friend_Request.ACCEPT:
            user.friends.add(request.user)
            user.save()
            return Response(
                {"details": "ok."},
                status=status.HTTP_200_OK,
            )
        if request.user.friendrequests.filter(id=user.id).exists():
            user.friends.add(request.user)
            request.user.friendrequests.remove(user)
            request.user.save()
        else:
            user.friendrequests.add(request.user)
        user.save()
        channel_layer = get_channel_layer()

        channels = cache.get(f"user_{request.user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "friend.request.sent",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

        channels = cache.get(f"user_{user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "friend.request.received",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

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
def UserDuelRequestAdd(request, name: str):
    if name == request.user.username:
        return Response(
            {"error": "You cannot duel yourself."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user = User.objects.get(username=name)
        if user.blocked.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are blocked."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if (
            user.msg_default_response == User.Message_Request.BLOCK
            and not user.friends.filter(id=request.user.id).exists()
        ):
            return Response(
                {"error": "You cannot start a duel with this user."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if user.duelrequests.filter(id=request.user.id).exists():
            return Response(
                {"error": "You already sent a duel request to this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.duels.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are already dueling this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        channel_layer = get_channel_layer()

        channel = (
            GroupChannel.objects.filter(channel_type=GroupChannel.Type.DM)
            .filter(users=request.user)
            .filter(users=user)
            .distinct()
            .first()
        )
        if not channel:
            channel = GroupChannel.objects.create(channel_type=GroupChannel.Type.DM)
            channel.users.add(user)
            channel.users.add(request.user)

            channel.save()

            layer_channels = cache.get(f"user_{request.user.id}_channel")

            if layer_channels:
                for layer_channel in layer_channels:
                    async_to_sync(channel_layer.send)(
                        layer_channel,
                        {
                            "type": "dm.creation.sent",
                            "from": request.user.username,
                            "to": user.username,
                            "channel_id": channel.id,
                        },
                    )

            layer_channels = cache.get(f"user_{user.id}_channel")

            if layer_channels:
                for layer_channel in layer_channels:
                    async_to_sync(channel_layer.send)(
                        layer_channel,
                        {
                            "type": "dm.creation.received",
                            "from": request.user.username,
                            "to": user.username,
                            "channel_id": channel.id,
                        },
                    )

        if request.user.duelrequests.filter(id=user.id).exists():
            game = Game.objects.create(
                uuid=uuid.uuid4(),
                region=request.user.region,
                state=Game.State.WAITING,
                game_type=Game.Type.DUEL,
            )
            game.users.add(request.user)
            game.users.add(user)
            game.save()
            request.user.duels.add(user)
            request.user.duelrequests.remove(user)
            request.user.save()
            user.duels.add(request.user)
            user.save()

            message = channel.messages.create(
                content="",
                original_content="",
                author=user,
                message_type=Messages.Type.DUEL,
            )
            message.save()

            for user in channel.users.all():
                layer_channels = cache.get(f"user_{user.id}_channel")

                if layer_channels:
                    for layer_channel in layer_channels:
                        async_to_sync(channel_layer.send)(
                            layer_channel,
                            {
                                "type": "channel.message.sent",
                                "from": request.user.username,
                                "channel_id": channel.id,
                                "message_id": message.id,
                            },
                        )

            channel.save()

            layer_channels = cache.get(f"user_{request.user.id}_channel")

            if layer_channels:
                for chnl in layer_channels:
                    async_to_sync(channel_layer.send)(
                        chnl,
                        {
                            "type": "duel.start.sent",
                            "from": request.user.username,
                            "to": user.username,
                            "game_id": str(game.uuid),
                        },
                    )

            layer_channels = cache.get(f"user_{user.id}_channel")

            if layer_channels:
                for chnl in layer_channels:
                    async_to_sync(channel_layer.send)(
                        chnl,
                        {
                            "type": "duel.start.received",
                            "from": request.user.username,
                            "to": user.username,
                            "game_id": str(game.uuid),
                        },
                    )

            return Response(
                {"details": "ok."},
                status=status.HTTP_200_OK,
            )

        else:
            user.duelrequests.add(request.user)
        user.save()

        message = channel.messages.create(
            content="",
            original_content="",
            author=request.user,
            message_type=Messages.Type.REQUEST,
        )
        message.save()

        for user in channel.users.all():
            layer_channels = cache.get(f"user_{user.id}_channel")

            if layer_channels:
                for layer_channel in layer_channels:
                    async_to_sync(channel_layer.send)(
                        layer_channel,
                        {
                            "type": "channel.message.sent",
                            "from": request.user.username,
                            "channel_id": channel.id,
                            "message_id": message.id,
                        },
                    )

        channel.save()

        channels = cache.get(f"user_{request.user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "duel.request.sent",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

        channels = cache.get(f"user_{user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "duel.request.received",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

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
def UserDuelRequestAccept(request, name: str):
    if name == request.user.username:
        return Response(
            {"error": "You cannot duel yourself."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user = User.objects.get(username=name)
        if user.blocked.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are blocked."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if user.duels.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are already dueling this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.duelrequests.filter(id=user.id).exists():
            return Response(
                {"error": "You have no duel request from this user."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        channel_layer = get_channel_layer()

        game = Game.objects.create(
            uuid=uuid.uuid4(),
            region=request.user.region,
            state=Game.State.WAITING,
            game_type=Game.Type.DUEL,
        )
        game.users.add(request.user)
        game.users.add(user)
        game.save()
        request.user.duels.add(user)
        request.user.duelrequests.remove(user)
        request.user.save()
        user.duels.add(request.user)
        user.save()
        channels = cache.get(f"user_{request.user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "duel.start.sent",
                        "from": request.user.username,
                        "to": user.username,
                        "game_id": str(game.uuid),
                    },
                )

        channels = cache.get(f"user_{user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "duel.start.received",
                        "from": request.user.username,
                        "to": user.username,
                        "game_id": str(game.uuid),
                    },
                )

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
        channel_layer = get_channel_layer()

        channels = cache.get(f"user_{request.user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "friend.remove.sent",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

        channels = cache.get(f"user_{user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "friend.remove.received",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

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
        channel_layer = get_channel_layer()

        channels = cache.get(f"user_{request.user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "friend.accepted.sent",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

        channels = cache.get(f"user_{user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "friend.accepted.received",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

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

        channel_layer = get_channel_layer()

        channels = cache.get(f"user_{request.user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "friend.request.rejected.sent",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

        channels = cache.get(f"user_{user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "friend.request.rejected.received",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

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

        channel_layer = get_channel_layer()

        channels = cache.get(f"user_{request.user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "friend.request.removed.sent",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

        channels = cache.get(f"user_{user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "friend.request.removed.received",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

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
        if user.duels.filter(id=request.user.id).exists():
            return Response(
                {"error": "You cannot block an user in a duel."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.friends.filter(id=request.user.id).exists():
            user.friends.remove(request.user)
        if user.friendrequests.filter(id=request.user.id).exists():
            user.friendrequests.remove(request.user)
        if request.user.friendrequests.filter(id=user.id).exists():
            request.user.friendrequests.remove(user)
        if user.duelrequests.filter(id=request.user.id).exists():
            user.duelrequests.remove(request.user)
        if request.user.duelrequests.filter(id=user.id).exists():
            request.user.duelrequests.remove(user)
        for channel in (
            GroupChannel.objects.filter(channel_type=GroupChannel.Type.GROUP)
            .filter(users=request.user)
            .filter(users=user)
            .all()
        ):
            channel.users.remove(request.user)
            if channel.users.count() == 0:
                channel.delete()
            elif channel.created_by.id == request.user.id:
                channel.created_by = channel.users.first()
            channel.save()
        request.user.blocked.add(user)
        user.save()
        request.user.save()

        channel_layer = get_channel_layer()

        channels = cache.get(f"user_{request.user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "block.user.sent",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

        channels = cache.get(f"user_{user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "block.user.received",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

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

        channel_layer = get_channel_layer()

        channels = cache.get(f"user_{request.user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "unblock.user.sent",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

        channels = cache.get(f"user_{user.id}_channel")

        if channels:
            for channel in channels:
                async_to_sync(channel_layer.send)(
                    channel,
                    {
                        "type": "unblock.user.received",
                        "from": request.user.username,
                        "to": user.username,
                    },
                )

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
            if (
                user.msg_default_response == User.Message_Request.BLOCK
                and not user.friends.filter(id=request.user.id).exists()
            ):
                return Response(
                    {
                        "error": "You cannot start a private message channel with this user."
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            channel = GroupChannel.objects.create(channel_type=GroupChannel.Type.DM)
            channel.users.add(user)
            channel.users.add(request.user)

            channel.save()

            channel_layer = get_channel_layer()

            layer_channels = cache.get(f"user_{request.user.id}_channel")

            if layer_channels:
                for layer_channel in layer_channels:
                    async_to_sync(channel_layer.send)(
                        layer_channel,
                        {
                            "type": "dm.creation.sent",
                            "from": request.user.username,
                            "to": user.username,
                            "channel_id": channel.id,
                        },
                    )

            layer_channels = cache.get(f"user_{user.id}_channel")

            if layer_channels:
                for layer_channel in layer_channels:
                    async_to_sync(channel_layer.send)(
                        layer_channel,
                        {
                            "type": "dm.creation.received",
                            "from": request.user.username,
                            "to": user.username,
                            "channel_id": channel.id,
                        },
                    )

        return Response({"channel_id": channel.id}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def channel(request):
    if request.method == "GET":
        return Response(
            {
                "channels": [
                    {
                        "id": channel.id,
                        "name": channel.name
                        if channel.channel_type == GroupChannel.Type.GROUP
                        else channel.users.exclude(id=request.user.id).first().username,
                        "description": channel.description,
                        "avatar_url": channel.avatar_url.url
                        if channel.avatar_url
                        else None,
                        "created_at": channel.created_at,
                        "created_by": channel.created_by.username
                        if channel.created_by
                        else None,
                        "channel_type": channel.channel_type,
                        "topic": channel.topic,
                        "users": [user.username for user in channel.users.all()],
                    }
                    for channel in GroupChannel.objects.order_by("-updated_at").filter(
                        users=request.user.id
                    )
                    if channel.channel_type != GroupChannel.Type.DM
                    or channel.messages.exists()
                ]
            },
            status=status.HTTP_200_OK,
        )
    elif request.method == "PUT":
        if (
            "name" not in request.data
            or not isinstance(request.data["name"], str)
            or not len(request.data["name"])
        ):
            return Response(
                {"error": "You tried to create a channel with an empty name."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        channel = GroupChannel.objects.create(
            name=request.data["name"],
            channel_type=GroupChannel.Type.GROUP,
            created_by=request.user,
        )
        channel.users.add(request.user)
        channel.save()

        channel_layer = get_channel_layer()

        layer_channels = cache.get(f"user_{request.user.id}_channel")

        if layer_channels:
            for layer_channel in layer_channels:
                async_to_sync(channel_layer.send)(
                    layer_channel,
                    {
                        "type": "channel.creation.sent",
                        "from": request.user.username,
                        "channel_id": channel.id,
                    },
                )

        return Response(
            {
                "channel": {
                    "id": channel.id,
                    "name": channel.name,
                    "description": channel.description,
                    "avatar_url": channel.avatar_url.url
                    if channel.avatar_url
                    else None,
                    "created_at": channel.created_at,
                    "created_by": channel.created_by.username
                    if channel.created_by
                    else None,
                    "channel_type": channel.channel_type,
                    "topic": channel.topic,
                }
            },
            status=status.HTTP_201_CREATED,
        )


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def channel_id(request, id: int):
    try:
        channel = GroupChannel.objects.get(id=id)
        if not channel.users.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are not allowed to see this channel."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if request.method == "GET":
            return Response(
                {
                    "channel": {
                        "id": channel.id,
                        "name": channel.name
                        if channel.channel_type == GroupChannel.Type.GROUP
                        else channel.users.exclude(id=request.user.id).first().username,
                        "description": channel.description,
                        "avatar_url": channel.avatar_url.url
                        if channel.avatar_url
                        else None,
                        "created_at": channel.created_at,
                        "created_by": channel.created_by.username
                        if channel.created_by
                        else None,
                        "channel_type": channel.channel_type,
                        "topic": channel.topic,
                        "users": [user.username for user in channel.users.all()],
                        "cant_send": any(
                            user.blocked.filter(id=request.user.id)
                            for user in channel.users.all()
                        )
                        or any(
                            request.user.blocked.filter(id=user.id)
                            for user in channel.users.all()
                        ),
                    }
                },
                status=status.HTTP_200_OK,
            )

        elif request.method == "PATCH":
            for key, value in request.data.items():
                if key == "name" and isinstance(value, str):
                    channel.name = value[:64]
                elif key == "description" and isinstance(value, str):
                    channel.description = value[:256]
                elif key == "topic" and isinstance(value, str):
                    channel.topic = value[:512]
                elif (
                    key == "users"
                    and (
                        isinstance(value, list)
                        and all(isinstance(item, str) for item in value)
                    )
                    and channel.channel_type == GroupChannel.Type.GROUP
                ):
                    for username in value:
                        try:
                            user = User.objects.get(username=username)
                            if not user.blocked.filter(
                                id=request.user.id
                            ).exists() and (
                                user.msg_default_response != user.Message_Request.BLOCK
                                or user.friends.filter(id=request.user.id).exists()
                            ):
                                channel.users.add(user)
                        except User.DoesNotExist:
                            pass

            channel_layer = get_channel_layer()

            for user in channel.users.all():
                layer_channels = cache.get(f"user_{user.id}_channel")

                if layer_channels:
                    for layer_channel in layer_channels:
                        async_to_sync(channel_layer.send)(
                            layer_channel,
                            {
                                "type": "channel.edit.sent",
                                "from": request.user.username,
                                "channel_id": channel.id,
                            },
                        )

            channel.save()
            return Response(
                {
                    "channel": {
                        "id": channel.id,
                        "name": channel.name
                        if channel.channel_type == GroupChannel.Type.GROUP
                        else channel.users.exclude(id=request.user.id).first().username,
                        "description": channel.description,
                        "avatar_url": channel.avatar_url.url
                        if channel.avatar_url
                        else None,
                        "created_at": channel.created_at,
                        "created_by": channel.created_by.username
                        if channel.created_by
                        else None,
                        "channel_type": channel.channel_type,
                        "topic": channel.topic,
                        "users": [user.username for user in channel.users.all()],
                    }
                },
                status=status.HTTP_200_OK,
            )

        elif request.method == "DELETE":
            if channel.created_by.id != request.user.id:
                return Response(
                    {"error": "You are not allowed to delete this channel."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            channel_layer = get_channel_layer()

            for user in channel.users.all():
                layer_channels = cache.get(f"user_{user.id}_channel")

                if layer_channels:
                    for layer_channel in layer_channels:
                        async_to_sync(channel_layer.send)(
                            layer_channel,
                            {
                                "type": "channel.delete.sent",
                                "from": request.user.username,
                                "channel_id": channel.id,
                            },
                        )

            channel.delete()
            return Response({"details": "ok"}, status=status.HTTP_200_OK)

    except GroupChannel.DoesNotExist:
        return Response(
            {"error": "Channel not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def channel_messages(request, id: int):
    try:
        channel = GroupChannel.objects.get(id=id)
        if not channel.users.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are not allowed to see this channel."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        has_seen = False

        if request.method == "GET":
            for message in channel.messages.all():
                if not message.seen_by.filter(id=request.user.id).exists():
                    message.seen_by.add(request.user)
                    has_seen = True

            if has_seen:
                channel_layer = get_channel_layer()

                for user in channel.users.all():
                    layer_channels = cache.get(f"user_{user.id}_channel")

                    if layer_channels:
                        for layer_channel in layer_channels:
                            async_to_sync(channel_layer.send)(
                                layer_channel,
                                {
                                    "type": "channel.view.sent",
                                    "from": request.user.username,
                                    "channel_id": channel.id,
                                },
                            )

            return Response(
                {
                    "messages": [
                        {
                            "id": message.id,
                            "content": message.content,
                            "author": message.author.username,
                            "created_at": message.created_at,
                            "seen_by": [
                                user.username for user in message.seen_by.all()
                            ],
                            "edited": message.edited,
                            "is_pin": message.is_pin,
                        }
                        for message in channel.messages.all().order_by("-id")[:100:-1]
                    ],
                },
                status=status.HTTP_200_OK,
            )

        elif request.method == "POST":
            if (
                "content" not in request.data
                or not isinstance(request.data["content"], str)
                or not len(request.data["content"])
            ):
                return Response(
                    {"error": "You tried to send an empty message."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if (
                channel.channel_type == GroupChannel.Type.DM
                and channel.users.exclude(id=request.user.id)
                .first()
                .blocked.filter(id=request.user.id)
                .exists()
            ):
                return Response(
                    {"error": "You are blocked."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            if (
                channel.channel_type == GroupChannel.Type.DM
                and request.user.blocked.filter(
                    id=channel.users.exclude(id=request.user.id).first().id
                ).exists()
            ):
                return Response(
                    {"error": "You have blocked this user."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            message = channel.messages.create(
                content=request.data["content"][:2048],
                original_content=request.data["content"][:2048],
                author=request.user,
            )
            message.seen_by.add(request.user)
            message.save()

            channel_layer = get_channel_layer()

            for user in channel.users.all():
                layer_channels = cache.get(f"user_{user.id}_channel")

                if layer_channels:
                    for layer_channel in layer_channels:
                        async_to_sync(channel_layer.send)(
                            layer_channel,
                            {
                                "type": "channel.message.sent",
                                "from": request.user.username,
                                "channel_id": channel.id,
                                "message_id": message.id,
                            },
                        )

            channel.save()
            return Response(
                {
                    "id": message.id,
                    "content": message.content,
                    "author": message.author.username,
                    "created_at": message.created_at,
                    "seen_by": [user.username for user in message.seen_by.all()],
                    "edited": message.edited,
                    "is_pin": message.is_pin,
                },
                status=status.HTTP_201_CREATED,
            )

    except GroupChannel.DoesNotExist:
        return Response(
            {"error": "Channel not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def channel_messages_id(request, channel_id: int, message_id: int):
    try:
        channel = GroupChannel.objects.get(id=channel_id)
        if not channel.users.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are not allowed to see this channel."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        message: Messages = channel.messages.filter(id=message_id).first()

        if not message:
            return Response(
                {"error": "Message not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.method == "GET":
            return Response(
                {
                    "message": {
                        "content": message.content,
                        "author": message.author.username,
                        "created_at": message.created_at,
                        "seen_by": [user.username for user in message.seen_by.all()],
                        "edited": message.edited,
                        "is_pin": message.is_pin,
                    }
                },
                status=status.HTTP_200_OK,
            )

        elif request.method == "PATCH":
            if "content" in request.data:
                if message.author.id != request.user.id:
                    return Response(
                        {"error": "You are not allowed to edit this message."},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )

                if (
                    "content" not in request.data
                    or not isinstance(request.data["content"], str)
                    or not len(request.data["content"])
                ):
                    return Response(
                        {"error": "You tried to edit a message to be empty."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                message.content = request.data["content"][:2048]

            if "is_pin" in request.data and isinstance(request.data["is_pin"], bool):
                message.is_pin = request.data["is_pin"]

            channel_layer = get_channel_layer()

            for user in channel.users.all():
                layer_channels = cache.get(f"user_{user.id}_channel")

                if layer_channels:
                    for layer_channel in layer_channels:
                        async_to_sync(channel_layer.send)(
                            layer_channel,
                            {
                                "type": "channel.message.edited",
                                "from": request.user.username,
                                "channel_id": channel.id,
                                "message_id": message.id,
                            },
                        )

            message.save()
            return Response(
                {
                    "message": {
                        "content": message.content,
                        "author": message.author.username,
                        "created_at": message.created_at,
                        "seen_by": [user.username for user in message.seen_by.all()],
                        "edited": message.edited,
                        "is_pin": message.is_pin,
                    }
                },
                status=status.HTTP_200_OK,
            )

        elif request.method == "DELETE":
            if message.author.id != request.user.id:
                return Response(
                    {"error": "You are not allowed to delete this message."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            channel_layer = get_channel_layer()

            for user in channel.users.all():
                layer_channels = cache.get(f"user_{user.id}_channel")

                if layer_channels:
                    for layer_channel in layer_channels:
                        async_to_sync(channel_layer.send)(
                            layer_channel,
                            {
                                "type": "channel.message.deleted",
                                "from": request.user.username,
                                "channel_id": channel.id,
                                "message_id": message.id,
                            },
                        )

            message.delete()
            return Response(
                {"details": "ok."},
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

    return Response(
        {
            "leaderboard": json.dumps(
                {name["username"]: name["elo"] for name in leaderboard}
            )
        },
        status=status.HTTP_200_OK,
    )
