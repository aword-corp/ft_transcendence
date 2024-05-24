from django.urls import path

from . import views

urlpatterns = [
    path("matchmaking", views.MatchmakingView, name="pong_matchmaking"),
]
