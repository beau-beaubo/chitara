from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    MeView,
    OAuthRegistrationView,
    UserDetailView,
    UserListView,
    UserRegisterView,
    UserUpdateView,
    google_jwt_redirect,
)

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="user-register"),
    path("oauth-register/", OAuthRegistrationView.as_view(), name="oauth-register"),
    path("login/", LoginView.as_view(), name="user-login"),
    path("list/", UserListView.as_view(), name="user-list"),
    path("<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("<int:pk>/update/", UserUpdateView.as_view(), name="user-update"),
    path("auth/google/jwt-redirect/", google_jwt_redirect, name="google-jwt-redirect"),
    path("me/", MeView.as_view(), name="me"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
