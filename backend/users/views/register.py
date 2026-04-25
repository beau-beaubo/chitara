from django.contrib.auth import login
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from users.helpers import get_user_model_cls, json_error, parse_json_body
from users.jwt_utils import issue_jwt_for_user
from users.serializers import user_to_dict


@method_decorator(csrf_exempt, name="dispatch")
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
