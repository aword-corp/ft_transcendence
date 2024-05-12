from django.urls import path

from . import views

urlpatterns = [
    path("register", views.register_view, name="register_view"),
    path("login", views.login_view, name="login_view"),
    path("login/2fa", views.login_2fa_view, name="login_2fa_view"),
    path("logout", views.logout_view, name="logout_view"),
]
