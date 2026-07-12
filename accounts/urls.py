from django.urls import path
from .views import (
    RegisterAPIView,
    LoginAPIView,
    LogoutAPIView,
    CurrentUserAPIView,
    ProfileAPIView,
    ChangePasswordAPIView
)

from rest_framework_simplejwt.views import TokenRefreshView


app_name='accounts'

urlpatterns = [

    path(
        "register/",
        RegisterAPIView.as_view(),
        name="register",
    ),

    path(
        "login/",
        LoginAPIView.as_view(),
        name="login",
    ),

    path(
        "logout/",
        LogoutAPIView.as_view(),
        name="logout",
    ),

    path(
        "me/",
        CurrentUserAPIView.as_view(),
        name="current-user",
    ),

    path(
        "profile/",
        ProfileAPIView.as_view(),
        name="profile",
    ),

    path(
        "change-password/",
        ChangePasswordAPIView.as_view(),
        name="change-password",
    ),

    path(
        "refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),
]