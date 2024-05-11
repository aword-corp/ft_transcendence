from django.db import models
from channels.db import database_sync_to_async
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
from datetime import date

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
    def create_user(self, email: str, password: str, username: str, region: str, country_code: str, language: str, birth_date: date, device_os:str, device_client:str, avatar_url: str):
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            region=region,
            country_code=country_code,
            language=language,
            birth_date=birth_date,
            avatar_url=avatar_url,
        )
        device: Device = Device(
            os=device_os,
            client=device_client,
        )
        device.save()
        user.devices.add(device)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, username: str, region: str, country_code: str, language: str, birth_date: str, device_os:str, device_client:str, avatar_url: str):
        user = self.create_user(
            email=email,
            password=password,
            username=username,
            region=region,
            country_code=country_code,
            language=language,
            birth_date=birth_date,
            device_os=device_os,
            device_client=device_client,
            avatar_url=avatar_url,
        )
        user.grade = 4
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    
    # Information
    username = models.CharField(max_length=32, unique=True)
    display_name = models.CharField(max_length=64, null=True)
    bio = models.CharField(max_length=2048, null=True)
    email = models.EmailField(
        verbose_name='email address',
        max_length=320,
        unique=True,
    )
    region = models.CharField(max_length=6)
    country_code = models.CharField(max_length=3)
    language = models.CharField(max_length=5)
    avatar_url = models.CharField(max_length=256, null=True)
    banner_url = models.CharField(max_length=256, null=True)
    birth_date = models.DateField()
    GRADE_CHOICES = [
        (1, 'User'),
        (2, 'Premium'),
        (3, 'Moderator'),
        (4, 'Admin')
    ]
    grade = models.SmallIntegerField(choices=GRADE_CHOICES, default=1)

    # Stats
    created_at = models.DateTimeField(auto_now_add=True)
    xp = models.FloatField(default=0.0)
    elo = models.FloatField(default=0.0)
    elo_history = models.ManyToManyField(Elo, related_name="user_elo_history")
    badges = models.ManyToManyField(Badge, related_name="user_badges")

    # Social
    friendrequests = models.ManyToManyField('self', symmetrical=True)
    friends = models.ManyToManyField('self', symmetrical=True)
    blocked = models.ManyToManyField('self')
    verified = models.BooleanField(default=False)
    STATUS_CHOICES = [
        (1, 'Offline'),
        (2, 'Playing'),
        (3, 'Spectating'),
        (4, 'Online'),
        (5, 'Away'),
        (6, 'Focus'),
        (7, 'Invisible')
    ]
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=4)

    # Settings / Cosmetic
    paddle_type = models.SmallIntegerField(default=1)
    theme = models.SmallIntegerField(default=1)
    goal_effect = models.SmallIntegerField(default=1)
    win_effect = models.SmallIntegerField(default=1)

    # Settings / Privacy
    FRIEND_REQUEST_CHOICES = [
        (1, 'Wait'),
        (2, 'Reject'),
        (3, 'Accept')
    ]
    friend_default_response = models.SmallIntegerField(choices=FRIEND_REQUEST_CHOICES, default=1)
    MSG_REQUEST_CHOICES = [
        (1, 'Confirm'),
        (2, 'Accept'),
        (3, 'Block')
    ]
    msg_default_response = models.SmallIntegerField(choices=MSG_REQUEST_CHOICES, default=1)
    devices = models.ManyToManyField(Device, related_name="user_devices")
    vc_auto_join = models.BooleanField(default=False)
    allow_duel = models.BooleanField(default=True)
    msg_sound = models.BooleanField(default=True)
    duel_sound = models.BooleanField(default=True)

    objects = PongUserManager()
    
class Chat(models.Model):
    content = models.CharField(max_length=512)
    user = models.ForeignKey(User, related_name='global_chat', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    @database_sync_to_async
    def create_message(user: User, message: str) -> None:
        Chat.objects.create(content=message[:512], user=user) # TODO Non null user

class Messages(models.Model):
    content = models.CharField(max_length=2048)
    author = models.ForeignKey(User, related_name="message_authors", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    seen_by = models.ManyToManyField(User, related_name="message_seen_by")
    edited = models.BooleanField(default=False)
    original_content = models.CharField(max_length=2048)

class PrivateMessage(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=256, null=True)
    avatar_url = models.CharField(max_length=256, null=True)
    users = models.ManyToManyField(User, related_name="channel_users")
    messages = models.ManyToManyField(Messages, related_name="channel_messages")
    created_at = models.DateTimeField(auto_now_add=True)

class Report(models.Model):
    user = models.ForeignKey(User, related_name="reported_users", on_delete=models.SET_NULL, null=True)
    reason = models.CharField(max_length=2048)
    created_at = models.DateTimeField(auto_now_add=True)
    REPORT_CHOICES = [
        (1, 'Pending'),
        (2, 'Escalated'),
        (3, 'Closed')
    ]
    state = models.SmallIntegerField(choices=REPORT_CHOICES, default=1)

class ChatReport(Report):
    message = models.ForeignKey(Messages, related_name="reported_messages", on_delete=models.SET_NULL, null=True)

class Game(models.Model):
    uuid = models.UUIDField(unique=True)
    date = models.DateTimeField(auto_now_add=True)
    users = models.ManyToManyField(User, related_name="game_users")
    winner = models.ForeignKey(User, related_name='game_winners', on_delete=models.SET_NULL, null=True)
    loser = models.ForeignKey(User, related_name='game_losers', on_delete=models.SET_NULL, null=True)
    ball_speed = models.FloatField()
    ball_size = models.FloatField()
    paddle_speed = models.FloatField()
    paddle_size = models.FloatField()
    region = models.CharField(max_length=6)
    STATE_CHOICES = [
        (1, 'Starting'),
        (2, 'Waiting'),
        (3, 'Playing'),
        (4, 'Ended'),
    ]
    state = models.SmallIntegerField(choices=STATE_CHOICES, default=1)

    @staticmethod
    @database_sync_to_async
    def get_game(req_uuid) -> 'Game':
        return Game.objects.get(uuid=req_uuid)

class Tournament(models.Model):
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=2048, null=True)
    games = models.ManyToManyField(Game, related_name="tournament_games")
    author = models.ForeignKey(User, related_name="tournament_authors", on_delete=models.SET_NULL, null=True)
    winner = models.ForeignKey(User, related_name='tournament_winners', on_delete=models.SET_NULL, null=True)
    users = models.ManyToManyField(User, related_name="tournament_users")
    created_at = models.DateTimeField(auto_now_add=True)
    starting_at = models.DateTimeField(auto_now_add=False)
    ended_at = models.DateTimeField(auto_now_add=False)
    region = models.CharField(max_length=6)
    STATE_CHOICES = [
        (1, 'Waiting'),
        (2, 'Starting'),
        (3, 'Playing'),
        (4, 'Break'),
        (5, 'Ended'),
    ]
    state = models.SmallIntegerField(choices=STATE_CHOICES, default=1)
