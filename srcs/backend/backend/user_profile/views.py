from django.core.exceptions import ValidationError
from db.models import UserTwoFactorAuthData, User
from django.shortcuts import render, redirect
import pyotp
from django.http import HttpResponseNotAllowed


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


def setup_2fa(request):
    if not request.user.is_authenticated:
        return redirect("home")
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
    return HttpResponseNotAllowed(["GET", "POST"])
