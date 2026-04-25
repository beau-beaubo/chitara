import json

from django.contrib.auth import get_user_model
from django.http import HttpRequest, JsonResponse


def get_user_model_cls():
    return get_user_model()


def json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"error": message}, status=status)


def parse_json_body(request: HttpRequest) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("Invalid JSON body")


def get_authenticated_user(request: HttpRequest):
    if request.user.is_authenticated:
        return request.user
    return None
