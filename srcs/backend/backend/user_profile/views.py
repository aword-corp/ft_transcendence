from django.core.exceptions import ValidationError
from db.models import UserTwoFactorAuthData, User
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
import pyotp


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


@api_view(["POST", "GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([TenPerDayUserThrottle])
def setup_2fa(request):
    if request.method == "POST":
        context = {}
        user = request.user

        try:
            two_factor_auth_data = user_two_factor_auth_data_create(user=user)
            otp_secret = two_factor_auth_data.otp_secret

            context["otp_secret"] = otp_secret
            context["qr_code"] = two_factor_auth_data.generate_qr_code(name=user.email)
        except ValidationError as exc:
            context["form_errors"] = exc.messages

        return render(request, "profile/settings/setup_2fa.html", context=context)
    elif request.method == "GET":
        return render(request, "profile/settings/setup_2fa.html")


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
            return Response("removed")

    except User.DoesNotExist:
        pass

    return Response("couldn't remove")
