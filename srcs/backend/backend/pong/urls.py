from django.urls import path

from . import views

urlpatterns = [
    path("", views.pong.as_view(), name="pong"),
]
