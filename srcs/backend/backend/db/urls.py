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
    ft_callback,
    HomeView,
    UserProfileView,
    SelfUserFriendsList,
    UserFriendsList,
    UserFriendsAdd,
    UserFriendsRemove,
    UserBlock,
    UserFriendRequestAccept,
    UserFriendRequestReject,
    UserUnBlock,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("", HomeView, name="home"),
    path("auth/register", RegisterView, name="sign_up"),
    path("auth/login", LoginView, name="token_obtain_pair"),
    path("auth/ft/callback", ft_callback, name="ft_callback"),
    path("auth/validate", ValidateView, name="validate_view"),
    path("auth/logout", LogoutView.as_view(), name="logout"),
    path("auth/login/verify", VerifyView, name="token_verify_otp"),
    path("auth/login/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/remove_2fa", remove_2fa, name="remove_2fa"),
    path("auth/setup_2fa", setup_2fa, name="setup_2fa"),
    path("clicks", get_clicks, name="get_clicks"),
    path("leaderboard", get_leaderboard, name="get_leaderboard"),
    path("user/profile/<str:name>", UserProfileView, name="user_profile"),
    path("user/friends/list", SelfUserFriendsList, name="self_user_friends_list"),
    path("user/friends/list/<str:name>", UserFriendsList, name="user_friends_list"),
    path("user/friends/add/<str:name>", UserFriendsAdd, name="user_friends_add"),
    path(
        "user/friends/remove/<str:name>", UserFriendsRemove, name="user_friends_remove"
    ),
    path(
        "user/requests/friends/accept/<str:name>",
        UserFriendRequestAccept,
        name="user_requests_friends_accept",
    ),
    path(
        "user/requests/friends/reject/<str:name>",
        UserFriendRequestReject,
        name="user_requests_friends_reject",
    ),
    path("user/block/<str:name>", UserBlock, name="user_block"),
    path("user/unblock/<str:name>", UserUnBlock, name="user_unblock"),
]
