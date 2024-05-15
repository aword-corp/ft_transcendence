from django.urls import path
from .views import RegisterView, LoginView, VerifyView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    path("auth/register", RegisterView, name="sign_up"),
    path("auth/login", LoginView, name="token_obtain_pair"),
    path("auth/login/verify", VerifyView, name="token_verify_otp"),
    path("auth/login/refresh", TokenRefreshView.as_view(), name="token_refresh"),
]
