from __future__ import annotations

from django.shortcuts import render,redirect
from urllib.parse import urlencode
import secrets

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.http import HttpRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from users.jwt_utils import issue_jwt_for_user
from users.serializers import user_to_dict

import json
from django.contrib.auth import get_user_model

def get_user_model_cls():
    return get_user_model()

def json_error(message, status=400):
    return JsonResponse({"error": message}, status=status)

def parse_json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("Invalid JSON body")

def get_authenticated_user(request):
    if request.user.is_authenticated:
        return request.user
    return None

# ---------------------------------------------------------------------------
# Auth views
# ---------------------------------------------------------------------------

@method_decorator(csrf_exempt, name='dispatch')
class UserRegisterView(View):
    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            payload = parse_json_body(request)
        except ValueError as exc:
            return json_error(str(exc), status=400)

        required = ["username", "email", "password", "first_name", "last_name"]
        missing = [k for k in required if not payload.get(k)]
        if missing:
            return JsonResponse({"error": "Missing required fields", "missing": missing}, status=400)

        User = get_user_model_cls()
        if User.objects.filter(username=payload["username"]).exists():
            return json_error("username already exists", status=409)
        if User.objects.filter(email=payload["email"]).exists():
            return json_error("email already exists", status=409)

        user = User.objects.create_user(
            username=payload["username"],
            email=payload["email"],
            password=payload["password"],
            first_name=payload["first_name"],
            last_name=payload["last_name"],
        )
        login(request, user)
        token = issue_jwt_for_user(user.id)
        return JsonResponse({"token": token, "user": user_to_dict(user)}, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            payload = parse_json_body(request)
        except ValueError as exc:
            return json_error(str(exc), status=400)

        username = str(payload.get("username") or "").strip()
        password = str(payload.get("password") or "")
        if not username or not password:
            return json_error("username and password are required", status=400)

        user = authenticate(request, username=username, password=password)
        if user is None:
            return json_error("invalid credentials", status=401)

        login(request, user)
        token = issue_jwt_for_user(user.id)
        return JsonResponse({"authenticated": True, "token": token, "user": user_to_dict(user)})


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(View):
    def post(self, request: HttpRequest) -> JsonResponse:
        logout(request)
        request.session.flush()
        return JsonResponse({"logged_out": True})


class MeView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        user = get_authenticated_user(request)
        if user is None:
            return JsonResponse({"authenticated": False, "user": None}, status=200)
        return JsonResponse({"authenticated": True, "user": user_to_dict(user)})


# ---------------------------------------------------------------------------
# OAuth views
# ---------------------------------------------------------------------------

@method_decorator(csrf_exempt, name='dispatch')
class OAuthRegistrationView(View):
    """Complete OAuth registration with additional user data."""

    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            payload = parse_json_body(request)
        except ValueError as exc:
            return json_error(str(exc), status=400)

        oauth_session_key = payload.get("oauth_session")
        if not oauth_session_key:
            return json_error("OAuth session key is required", status=400)

        session_data = cache.get(f"oauth_session_{oauth_session_key}")
        if not session_data:
            return json_error("OAuth session expired or invalid", status=400)

        email = str(payload.get("email") or "").strip().lower()
        if not email:
            return json_error("email is required", status=400)

        if email != session_data.get("email", "").lower():
            return json_error("email must match OAuth session", status=400)

        User = get_user_model_cls()
        if User.objects.filter(email=email).exists():
            return json_error("email already exists", status=409)

        username = str(payload.get("username") or email.split("@")[0]).strip()
        if User.objects.filter(username=username).exists():
            return json_error("username already exists", status=409)

        details = session_data.get("details", {})
        user = User.objects.create(
            username=username,
            email=email,
            first_name=str(payload.get("first_name") or details.get("first_name", "")).strip(),
            last_name=str(payload.get("last_name") or details.get("last_name", "")).strip(),
            external_id = details.get("sub")  # Google user ID,
        )

        cache.delete(f"oauth_session_{oauth_session_key}")

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        token = issue_jwt_for_user(user.id)

        return JsonResponse({
            "success": True,
            "token": token,
            "user": user_to_dict(user),
        }, status=201)


def google_jwt_redirect(request: HttpRequest):
    # social-auth leaves the user logged into the Django session here
    user = request.user 
    if not user.is_authenticated:
        return JsonResponse({"error": "authentication required"}, status=401)

    token = issue_jwt_for_user(user.id)
    # Redirect to your ChitaraApp frontend
    target = f"{settings.FRONTEND_ORIGIN}/?token={token}"
    return HttpResponseRedirect(target)

def google_login(request):
    from social_django.utils import load_backend, load_strategy
    strategy = load_strategy(request)
    backend = load_backend(
        strategy,
        "google-oauth2",
        redirect_uri=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI
    )
    
    # Force Google to show the account chooser every time
    return redirect(backend.auth_url() + "&prompt=select_account")
# ---------------------------------------------------------------------------
# User management views
# ---------------------------------------------------------------------------

class UserListView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        user = get_authenticated_user(request)
        if user is None:
            return json_error("authentication required", status=401)
        if not user.is_staff:
            return json_error("forbidden", status=403)

        User = get_user_model_cls()
        users = [user_to_dict(u) for u in User.objects.all().order_by("id")]
        return JsonResponse({"results": users})


class UserDetailView(View):
    def get(self, request: HttpRequest, pk: int) -> JsonResponse:
        current = get_authenticated_user(request)
        if current is None:
            return json_error("authentication required", status=401)

        User = get_user_model_cls()
        user = get_object_or_404(User, pk=pk)

        if not current.is_staff and current.id != user.id:
            return json_error("forbidden", status=403)

        return JsonResponse({"user": user_to_dict(user)})


@method_decorator(csrf_exempt, name='dispatch')
class UserUpdateView(View):
    def patch(self, request: HttpRequest, pk: int) -> JsonResponse:
        current = get_authenticated_user(request)
        if not current: return json_error("Unauthorized", 401)

        try:
            payload = parse_json_body(request)
        except ValueError as exc:
            return json_error(str(exc))

        User = get_user_model_cls()
        user = get_object_or_404(User, pk=pk)

        # Check permissions
        if not current.is_staff and current.id != user.id:
            return json_error("forbidden", status=403)

        # Apply updates
        for field in ["first_name", "last_name", "email"]:
            if field in payload:
                setattr(user, field, str(payload[field]).strip())
        
        if "password" in payload and payload["password"]:
            user.set_password(str(payload["password"]))

        user.save()
        return JsonResponse({"user": user_to_dict(user)})