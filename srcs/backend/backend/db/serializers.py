from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User
from .utils import verify_date, verify_password, verify_username


class EditUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "display_name",
            "password",
            "bio",
            "region",
            "country_code",
            "language",
            "avatar_url",
            "banner_url",
            "birth_date",
        ]

    def validate_username(self, value):
        return verify_username(value)

    def validate_birth_date(self, value):
        return verify_date(value)

    def validate_password(self, value):
        password = value
        password_confirmation = self.initial_data["password_confirmation"]
        if password and password_confirmation and password != password_confirmation:
            raise serializers.ValidationError("Passwords don't match")
        return verify_password(password, self.initial_data["username"])

    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)
        try:
            user.set_password(validated_data["password"])
            user.save()
        except KeyError:
            pass
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
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
        ]
        extra_kwargs = {
            "email": {"required": True},
            "username": {"required": True},
            "password": {"required": True, "write_only": True},
            "region": {"required": True},
            "country_code": {"required": True},
            "language": {"required": True},
            "birth_date": {"required": True},
        }

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

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["email"] = user.email
        token["username"] = user.username

        return token
