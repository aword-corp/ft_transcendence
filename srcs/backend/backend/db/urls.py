from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    VerifyView,
    remove_2fa,
    setup_2fa,
    get_clicks,
	get_leaderboard,
	ValidateView,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    path("auth/register", RegisterView, name="sign_up"),
    path("auth/login", LoginView, name="token_obtain_pair"),
	path("auth/validate", ValidateView, name="validate_view"),
    path("auth/login/verify", VerifyView, name="token_verify_otp"),
    path("auth/login/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/remove_2fa", remove_2fa, name="remove_2fa"),
    path("auth/setup_2fa", setup_2fa, name="setup_2fa"),
    path("clicks", get_clicks, name="get_clicks"),
    path("leaderboard", get_leaderboard, name="get_leaderboard"),
]
