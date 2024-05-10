from django.db import models
from channels.db import database_sync_to_async
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)

class Count(models.Model):
    clicks = models.IntegerField(default=0)

    class Meta:
        managed = True

class Elo(models.Model):
    elo = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True

class Badge(models.Model):
    type = models.SmallIntegerField()
    added_at = models.DateTimeField(auto_now_add=True)
    display = models.BooleanField(default=True)

    class Meta:
        managed = True

class Device(models.Model):
    os = models.CharField(max_length=64)
    client = models.CharField(max_length=64)
    last_online = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True

class PongUserManager(BaseUserManager):
    def create_user(self, email, date_of_birth, password):
        user = self.model(
            email=self.normalize_email(email),
            date_of_birth=date_of_birth,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, date_of_birth, password):
        user = self.create_user(email,
            password=password,
            date_of_birth=date_of_birth
        )
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):

    # Information
    username = models.CharField(max_length=32, unique=True)
    display_name = models.CharField(max_length=64)
    bio = models.CharField(max_length=2048)
    email = models.EmailField(
        verbose_name='email address',
        max_length=320,
        unique=True,
    )
    region = models.CharField(max_length=6)
    country_code = models.CharField(max_length=3)
    language = models.CharField(max_length=5)
    avatar_url = models.CharField(max_length=256)
    banner_url = models.CharField(max_length=256)
    birth_date = models.DateField()
    GRADE_CHOICES = (
        (1, 'User'),
        (2, 'Premium'),
        (3, 'Moderator'),
        (4, 'Admin')
    )
    grade = models.SmallIntegerField(choices=GRADE_CHOICES, default=1)

    # Stats
    created_at = models.DateTimeField(auto_now_add=True)
    xp = models.FloatField()
    elo = models.ManyToManyField(Elo)
    badges = models.ManyToManyField(Badge)

    # Social
    friendrequests = models.ManyToManyField('self', symmetrical=True)
    friends = models.ManyToManyField('self', symmetrical=True)
    blocked = models.ManyToManyField('self')
    verified = models.BooleanField(default=False)
    STATUS_CHOICES = (
        (1, 'Offline'),
        (2, 'Playing'),
        (3, 'Spectating'),
        (4, 'Online'),
        (5, 'Away'),
        (6, 'Focus'),
        (7, 'Invisible')
    )
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=4)

    # Settings / Cosmetic
    paddle_type = models.SmallIntegerField(default=1)
    theme = models.SmallIntegerField(default=1)
    goal_effect = models.SmallIntegerField(default=1)
    win_effect = models.SmallIntegerField(default=1)

    # Settings / Privacy
    FRIEND_REQUEST_CHOICES = (
        (1, 'Wait'),
        (2, 'Reject'),
        (3, 'Accept')
    )
    friend_default_response = models.SmallIntegerField(choices=FRIEND_REQUEST_CHOICES, default=1)
    MSG_REQUEST_CHOICES = (
        (1, 'Accept'),
        (2, 'Confirm'),
        (3, 'Block')
    )
    msg_default_response = models.SmallIntegerField(choices=MSG_REQUEST_CHOICES, default=1)
    devices = models.ManyToManyField(Device)
    vc_auto_join = models.BooleanField(default=False)
    allow_duel = models.BooleanField(default=True)
    msg_sound = models.BooleanField(default=True)
    duel_sound = models.BooleanField(default=True)

    objects = PongUserManager()

    class Meta:
        managed = True
    
class Chat(models.Model):
    content = models.CharField(max_length=512)
    user = models.ForeignKey(User, related_name='global_chat', on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True

    @staticmethod
    @database_sync_to_async
    def create_message(user: User, message: str) -> None:
        Chat.objects.create(content=message[:512], user=user) # TODO Non null user

class Messages(models.Model):
    content = models.CharField(max_length=2048)
    author = models.ForeignKey(User, related_name="private_message", on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)
    seen_by = models.ManyToManyField(User)
    edited = models.BooleanField(default=False)

    class Meta:
        managed = True

class PrivateMessage(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=256)
    avatar_url = models.CharField(max_length=256)
    users = models.ManyToManyField(User)
    messages = models.ManyToManyField(Messages)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True

class Report(models.Model):
    user = models.ForeignKey(User, related_name="reported_users", on_delete=models.DO_NOTHING)
    reason = models.CharField(max_length=2048)
    created_at = models.DateTimeField(auto_now_add=True)
    REPORT_CHOICES = (
        (1, 'Pending'),
        (2, 'Escalated'),
        (3, 'Closed')
    )
    state = models.SmallIntegerField(choices=REPORT_CHOICES, default=1)

    class Meta:
        managed = True

class ChatReport(Report):
    message = models.ForeignKey(Messages, related_name="reported_messages", on_delete=models.DO_NOTHING)

class Game(models.Model):
    uuid = models.UUIDField(unique=True)
    date = models.DateTimeField(auto_now_add=True)
    users = models.ManyToManyField(User)
    winner = models.ForeignKey(User, related_name='won_games', on_delete=models.DO_NOTHING)
    loser = models.ForeignKey(User, related_name='lost_games', on_delete=models.DO_NOTHING)
    ball_speed = models.FloatField()
    ball_size = models.FloatField()
    paddle_speed = models.FloatField()
    paddle_size = models.FloatField()
    region = models.CharField(max_length=6)
    STATE_CHOICES = (
        (1, 'Starting'),
        (2, 'Waiting'),
        (3, 'Playing'),
        (4, 'Ended'),
    )
    state = models.SmallIntegerField(choices=STATE_CHOICES, default=1)

    class Meta:
        managed = True

    @staticmethod
    @database_sync_to_async
    def get_game(req_uuid) -> 'Game':
        return Game.objects.get(uuid=req_uuid)

class Tournament(models.Model):
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=2048)
    games = models.ManyToManyField(Game)
    author = models.ForeignKey(User, related_name="author_tournament", on_delete=models.DO_NOTHING)
    winner = models.ForeignKey(User, related_name='won_tournament', on_delete=models.DO_NOTHING)
    users = models.ManyToManyField(User, related_name="users_tournament")
    created_at = models.DateTimeField(auto_now_add=True)
    starting_at = models.DateTimeField(auto_now_add=False)
    ended_at = models.DateTimeField(auto_now_add=False)
    region = models.CharField(max_length=6)
    STATE_CHOICES = (
        (1, 'Waiting'),
        (2, 'Starting'),
        (3, 'Playing'),
        (4, 'Break'),
        (5, 'Ended'),
    )
    state = models.SmallIntegerField(choices=STATE_CHOICES, default=1)

    class Meta:
        managed = True
