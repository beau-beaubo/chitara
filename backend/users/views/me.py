from django.http import HttpRequest, JsonResponse
from django.views import View

from users.helpers import get_authenticated_user
from users.serializers import user_to_dict


class MeView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        user = get_authenticated_user(request)
        if user is None:
            return JsonResponse({"authenticated": False, "user": None})
        return JsonResponse({"authenticated": True, "user": user_to_dict(user)})
