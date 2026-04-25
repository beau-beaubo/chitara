from django.contrib.auth import login
from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from users.helpers import get_user_model_cls, json_error, parse_json_body
from users.jwt_utils import issue_jwt_for_user
from users.serializers import user_to_dict


@method_decorator(csrf_exempt, name="dispatch")
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
            external_id=details.get("sub"),
        )

        cache.delete(f"oauth_session_{oauth_session_key}")
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        token = issue_jwt_for_user(user.id)

        return JsonResponse({"success": True, "token": token, "user": user_to_dict(user)}, status=201)
