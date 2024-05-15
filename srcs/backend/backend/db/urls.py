from django.urls import path
from .views import RegisterView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("auth/register", RegisterView, name="sign_up"),
    path("auth/login", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/login/refresh", TokenRefreshView.as_view(), name="token_refresh"),
]
