from time import time_ns
from django.db import models
from django.conf import settings
from channels.db import database_sync_to_async
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from datetime import date, timedelta
from typing import List, Optional
import uuid
import pyotp
import qrcode
import qrcode.image.svg
from operator import itemgetter
from django.utils.translation import gettext_lazy as _


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


class Count(models.Model):
    clicks = models.IntegerField(default=0)


class Elo(models.Model):
    elo = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)


class Badge(models.Model):
    type = models.SmallIntegerField()
    added_at = models.DateTimeField(auto_now_add=True)
    display = models.BooleanField(default=True)


class Device(models.Model):
    os = models.CharField(max_length=64)
    client = models.CharField(max_length=64)
    last_online = models.DateTimeField(auto_now=True)


class PongUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(
        self,
        email: str,
        password: str,
        username: str,
        region: str,
        country_code: str,
        language: str,
        birth_date: date,
    ):
        if not email:
            raise ValueError("Email is Required")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            region=region,
            country_code=country_code,
            language=language,
            birth_date=birth_date,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str,
        username: str,
        region: str,
        country_code: str,
        language: str,
        birth_date: str,
    ):
        user = self.create_user(
            email=email,
            password=password,
            username=username,
            region=region,
            country_code=country_code,
            language=language,
            birth_date=birth_date,
        )
        user.grade = 4
        user.save(using=self._db)
        return user


class UserTwoFactorAuthData(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="two_factor_auth_data",
        on_delete=models.CASCADE,
    )

    otp_secret = models.CharField(max_length=255)
    session_identifier = models.UUIDField(blank=True, null=True)

    def generate_qr_code(self, name: Optional[str] = None) -> str:
        totp = pyotp.TOTP(self.otp_secret)
        qr_uri = totp.provisioning_uri(name=name, issuer_name=f"acorp.games: {name}")

        image_factory = qrcode.image.svg.SvgPathImage
        qr_code_image = qrcode.make(qr_uri, image_factory=image_factory)

        return qr_code_image.to_string().decode("utf_8")

    def validate_otp(self, otp: str) -> bool:
        totp = pyotp.TOTP(self.otp_secret)

        return totp.verify(otp)

    def rotate_session_identifier(self):
        self.session_identifier = uuid.uuid4()

        self.save(update_fields=["session_identifier"])


class User(AbstractBaseUser):
    # Information
    username = models.CharField(max_length=32, unique=True)
    display_name = models.CharField(max_length=64, null=True)
    bio = models.CharField(max_length=2048, null=True)
    email = models.EmailField(
        verbose_name="email address",
        max_length=320,
        unique=True,
    )

    class Region(models.TextChoices):
        EU_WE = "eu-we", _("Europe West")
        EU_EA = "eu-ea", _("Europe East")
        EU_NO = "eu-no", _("Europe North")
        NA_WE = "na-we", _("North America West")
        NA_CE = "na-ce", _("North America Central")
        NA_EA = "na-ea", _("North America East")
        CE_AM = "ce-am", _("Central America")
        SO_AM = "so-am", _("South America")
        NO_AF = "no-af", _("North Africa")
        SO_AF = "so-af", _("South Africa")
        MI_EA = "mi-ea", _("Middle East")
        AS_CN = "as-cn", _("China")
        AS_IN = "as-in", _("India")
        AS_SG = "as-sg", _("Singapore")
        AS_KR = "as-kr", _("Korea")
        AS_JP = "as-jp", _("Japan")
        OC_PA = "oc-pa", _("Oceania")

    region = models.CharField(choices=Region.choices, max_length=6)
    country_code = models.CharField(max_length=3)

    class Language(models.TextChoices):
        FR_FR = "FR-FR", _("Français")
        EN_US = "EN-US", _("English (United States)")
        CH_ZH = "CH-ZH", _("中文")

    language = models.CharField(choices=Language.choices, max_length=5)
    avatar_url = models.ImageField(
        max_length=256, null=True, upload_to="medias/users/avatar/"
    )
    banner_url = models.ImageField(
        max_length=256, null=True, upload_to="medias/users/banner/"
    )
    birth_date = models.DateField(null=True)

    class Grade(models.IntegerChoices):
        USER = 1, _("User")
        PREMIUM = 2, _("Premium")
        MODERATOR = 3, _("Moderator")
        ADMIN = 4, ("Admin")

    grade = models.SmallIntegerField(choices=Grade.choices, default=Grade.USER)

    # Stats
    created_at = models.DateTimeField(auto_now_add=True)
    xp = models.FloatField(default=0.0)
    elo = models.FloatField(default=800.0)
    elo_history = models.ManyToManyField(Elo, related_name="user_elo_history")
    badges = models.ManyToManyField(Badge, related_name="user_badges")

    # Social
    friendrequests = models.ManyToManyField(
        "self", symmetrical=False, related_name="user_friend_requests"
    )
    friends = models.ManyToManyField("self", symmetrical=True)
    blocked = models.ManyToManyField(
        "self", symmetrical=False, related_name="user_blocked_users"
    )
    verified = models.BooleanField(default=False)

    class Status(models.IntegerChoices):
        OFF = 1, _("Offline")
        GAME = 2, _("Playing")
        SPEC = 3, _("Spectating")
        ON = 4, _("Online")
        AWAY = 5, _("Away")
        FOCUS = 6, _("Focus")

    status = models.SmallIntegerField(choices=Status.choices, default=Status.ON)

    is_invisible = models.BooleanField(default=False)

    channel_name = models.CharField(max_length=128, null=True)

    # Settings / Cosmetic
    paddle_type = models.SmallIntegerField(default=1)
    theme = models.SmallIntegerField(default=1)
    goal_effect = models.SmallIntegerField(default=1)
    win_effect = models.SmallIntegerField(default=1)

    # Settings / Privacy

    class Friend_Request(models.IntegerChoices):
        WAIT = 1, _("Wait")
        REJECT = 2, _("Reject")
        ACCEPT = 3, _("Accept")

    friend_default_response = models.SmallIntegerField(
        choices=Friend_Request.choices, default=Friend_Request.WAIT
    )

    class Message_Request(models.IntegerChoices):
        CONFIRM = 1, _("Confirm")
        ACCEPT = 2, _("Accept")
        BLOCK = 3, _("Block")

    msg_default_response = models.SmallIntegerField(
        choices=Message_Request.choices, default=Message_Request.CONFIRM
    )

    class Friend_Display(models.IntegerChoices):
        FRIENDS = 1, _("Friends")
        PUBLIC = 2, _("Public")
        PRIVATE = 3, _("Private")

    display_friends = models.SmallIntegerField(
        choices=Friend_Display.choices, default=Friend_Display.FRIENDS
    )
    devices = models.ManyToManyField(Device, related_name="user_devices")
    vc_auto_join = models.BooleanField(default=False)
    allow_duel = models.BooleanField(default=True)
    msg_sound = models.BooleanField(default=True)
    duel_sound = models.BooleanField(default=True)
    has_2fa = models.BooleanField(default=False)
    has_ft = models.BooleanField(default=False)

    objects = PongUserManager()

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = [
        "region",
        "country_code",
        "language",
        "birth_date",
    ]

    @staticmethod
    @database_sync_to_async
    def get_user(login: str, password: str) -> Optional["User"]:
        try:
            user = User.objects.get(username=login)
            return user if user.check_password(password) else None
        except User.DoesNotExist:
            pass

        try:
            user = User.objects.get(email=login.lower())
            return user if user.check_password(password) else None
        except User.DoesNotExist:
            pass

        return None

    @staticmethod
    @database_sync_to_async
    @time_cache(time=timedelta(minutes=5))
    def get_leaderboard() -> List["User"]:
        print("---------Get leaderboard call---------")
        leaderboard = sorted(User.objects.values(), key=itemgetter("elo"))
        return leaderboard

    @database_sync_to_async
    def set_channel_name(self, channel_name: str) -> None:
        self.channel_name = channel_name

    @database_sync_to_async
    def is_in_queue(self):
        return bool(self.channel_name)

    @database_sync_to_async
    def get_channel_name(self) -> str:
        return self.channel_name

    @database_sync_to_async
    def is_friend(self, user: "User"):
        return user.friends.filter(id=self.id).exists()


class GlobalChat(models.Model):
    content = models.CharField(max_length=512)
    user = models.ForeignKey(
        User,
        related_name="global_chat_author",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    @database_sync_to_async
    def create_message(user, message: str) -> None:
        GlobalChat.objects.create(content=message[:512], user=user)


class Messages(models.Model):
    content = models.CharField(max_length=2048)
    author = models.ForeignKey(
        User, related_name="message_authors", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    seen_by = models.ManyToManyField(User, related_name="message_seen_by")
    edited = models.BooleanField(default=False)
    original_content = models.CharField(max_length=2048)


class GroupChannel(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=256, null=True)
    avatar_url = models.ImageField(
        max_length=256, null=True, upload_to="medias/groups/avatar/"
    )
    messages = models.ManyToManyField(Messages, related_name="channel_messages")
    created_at = models.DateTimeField(auto_now_add=True)
    users = models.ManyToManyField(User, related_name="channel_users")

    class Type(models.IntegerChoices):
        DM = 1, _("Direct Channel")
        GROUP = 2, _("Group Channel")

    channel_type = models.SmallIntegerField(choices=Type.choices)


class Report(models.Model):
    user = models.ForeignKey(
        User, related_name="reported_users", on_delete=models.SET_NULL, null=True
    )
    reason = models.CharField(max_length=2048)
    created_at = models.DateTimeField(auto_now_add=True)

    class Type(models.IntegerChoices):
        PENDING = 1, _("Pending")
        ESCALATED = 2, _("Escalated")
        CLOSED = 3, _("Closed")

    state = models.SmallIntegerField(choices=Type.choices, default=Type.PENDING)


class ChatReport(Report):
    message = models.ForeignKey(
        Messages, related_name="reported_messages", on_delete=models.SET_NULL, null=True
    )


class Game(models.Model):
    uuid = models.UUIDField(unique=True)
    date = models.DateTimeField(auto_now_add=True)
    users = models.ManyToManyField(User, related_name="game_users")
    winner = models.ForeignKey(
        User, related_name="game_winners", on_delete=models.SET_NULL, null=True
    )
    loser = models.ForeignKey(
        User, related_name="game_losers", on_delete=models.SET_NULL, null=True
    )
    ball_speed = models.FloatField(default=1.0)
    ball_size = models.FloatField(default=1.0)
    paddle_speed = models.FloatField(default=1.0)
    paddle_size = models.FloatField(default=1.0)
    region = models.CharField(max_length=6)
    score_winner = models.IntegerField(default=0)
    score_loser = models.IntegerField(default=0)

    class State(models.IntegerChoices):
        STARTING = 1, _("Starting")
        WAITING = 2, _("Waiting")
        PLAYING = 3, _("Playing")
        ENDED = 4, _("Ended")

    state = models.SmallIntegerField(choices=State.choices, default=State.STARTING)

    @staticmethod
    @database_sync_to_async
    def get_game(req_uuid) -> Optional["Game"]:
        try:
            game = Game.objects.get(uuid=req_uuid)
            return game
        except Game.DoesNotExist:
            pass

        return None


class Tournament(models.Model):
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=2048, null=True)
    games = models.ManyToManyField(Game, related_name="tournament_games")
    author = models.ForeignKey(
        User, related_name="tournament_authors", on_delete=models.SET_NULL, null=True
    )
    winner = models.ForeignKey(
        User, related_name="tournament_winners", on_delete=models.SET_NULL, null=True
    )
    users = models.ManyToManyField(User, related_name="tournament_users")
    created_at = models.DateTimeField(auto_now_add=True)
    starting_at = models.DateTimeField(auto_now_add=False)
    ended_at = models.DateTimeField(auto_now_add=False)
    region = models.CharField(max_length=6)

    class State(models.IntegerChoices):
        STARTING = 1, _("Starting")
        WAITING = 2, _("Waiting")
        PLAYING = 3, _("Playing")
        BREAK = 4, _("Break")
        ENDED = 5, _("Ended")

    state = models.SmallIntegerField(choices=State.choices, default=State.STARTING)
