from django.conf import settings
from django.http import HttpRequest, HttpResponseRedirect, JsonResponse
from django.utils import timezone

from users.jwt_utils import issue_jwt_for_user


def google_jwt_redirect(request: HttpRequest) -> HttpResponseRedirect:
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "authentication required"}, status=401)

    user.last_auth_date = timezone.now()
    user.save(update_fields=["last_auth_date"])
    token = issue_jwt_for_user(user.id)
    return HttpResponseRedirect(f"{settings.FRONTEND_ORIGIN}/?token={token}")
