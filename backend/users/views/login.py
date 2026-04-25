from django.contrib.auth import authenticate, login
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from users.helpers import json_error, parse_json_body
from users.jwt_utils import issue_jwt_for_user
from users.serializers import user_to_dict


@method_decorator(csrf_exempt, name="dispatch")
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

        user.last_auth_date = timezone.now()
        user.save(update_fields=["last_auth_date"])
        login(request, user)
        token = issue_jwt_for_user(user.id)
        return JsonResponse({"authenticated": True, "token": token, "user": user_to_dict(user)})
