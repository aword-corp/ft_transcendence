from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User
from .utils import verify_date, verify_password, verify_username


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "display_name",
            "bio",
            "password",
            "region",
            "country_code",
            "language",
            "avatar_url",
            "banner_url",
            "birth_date",
            "grade",
            "created_at",
            "xp",
            "elo",
            "verified",
            "status",
            "paddle_type",
            "theme",
            "goal_effect",
            "win_effect",
            "friend_default_response",
            "msg_default_response",
            "vc_auto_join",
            "allow_duel",
            "msg_sound",
            "duel_sound",
            "has_2fa",
        ]

    def validate_username(self, value):
        return verify_username(value)

    def validate_password(self, value):
        password = value
        password_confirmation = self.initial_data["password_confirmation"]
        if password and password_confirmation and password != password_confirmation:
            raise serializers.ValidationError("Passwords don't match")
        return verify_password(password, self.initial_data["username"])

    def validate_birth_date(self, value):
        return verify_date(value)

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data["email"],
            username=validated_data["username"],
            region=validated_data["region"],
            country_code=validated_data["country_code"],
            language=validated_data["language"],
            birth_date=validated_data["birth_date"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["email"] = user.email
        token["username"] = user.username
        token["display_name"] = user.display_name
        token["bio"] = user.bio
        token["region"] = user.region
        token["country_code"] = user.country_code
        token["language"] = user.language
        token["avatar_url"] = None
        token["banner_url"] = None
        token["avatar_url"] = user.avatar_url.url if user.avatar_url else None
        token["banner_url"] = user.banner_url.url if user.banner_url else None
        token["birth_date"] = user.birth_date.strftime("%m/%d/%Y")
        token["grade"] = user.grade
        token["created_at"] = user.created_at.strftime("%m/%d/%Y, %H:%M:%S")
        token["xp"] = user.xp
        token["elo"] = user.elo
        token["verified"] = user.verified
        token["status"] = user.status
        token["paddle_type"] = user.paddle_type
        token["theme"] = user.theme
        token["goal_effect"] = user.goal_effect
        token["win_effect"] = user.win_effect
        token["friend_default_response"] = user.friend_default_response
        token["msg_default_response"] = user.msg_default_response
        token["vc_auto_join"] = user.vc_auto_join
        token["allow_duel"] = user.allow_duel
        token["msg_sound"] = user.msg_sound
        token["duel_sound"] = user.duel_sound
        token["has_2fa"] = user.has_2fa

        return token
