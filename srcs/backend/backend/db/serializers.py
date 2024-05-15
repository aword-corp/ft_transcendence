from rest_framework import serializers
from .models import User


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
