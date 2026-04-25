from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from users.helpers import get_authenticated_user, get_user_model_cls, json_error, parse_json_body
from users.serializers import user_to_dict


@method_decorator(csrf_exempt, name="dispatch")
class UserUpdateView(View):
    def patch(self, request: HttpRequest, pk: int) -> JsonResponse:
        current = get_authenticated_user(request)
        if not current:
            return json_error("Unauthorized", status=401)

        try:
            payload = parse_json_body(request)
        except ValueError as exc:
            return json_error(str(exc))

        User = get_user_model_cls()
        user = get_object_or_404(User, pk=pk)

        if not current.is_staff and current.id != user.id:
            return json_error("forbidden", status=403)

        for field in ["first_name", "last_name", "email"]:
            if field in payload:
                setattr(user, field, str(payload[field]).strip())

        if "password" in payload and payload["password"]:
            user.set_password(str(payload["password"]))

        user.save()
        return JsonResponse({"user": user_to_dict(user)})
