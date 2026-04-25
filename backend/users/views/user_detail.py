from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from users.helpers import get_authenticated_user, get_user_model_cls, json_error
from users.serializers import user_to_dict


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
