from django.http import HttpRequest, JsonResponse
from django.views import View

from users.helpers import get_authenticated_user, get_user_model_cls, json_error
from users.serializers import user_to_dict


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
