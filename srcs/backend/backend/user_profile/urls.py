from django.urls import path

from . import views

urlpatterns = [
    path("settings/setup_2fa", views.setup_2fa, name="setup_2fa"),
    path("settings/remove_2fa", views.remove_2fa, name="remove_2fa"),
]
