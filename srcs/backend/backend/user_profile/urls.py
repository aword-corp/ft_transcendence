from django.urls import path

from . import views

urlpatterns = [
    path("settings/setup_2fa", views.setup_2fa, name="setup_2fa"),
]
