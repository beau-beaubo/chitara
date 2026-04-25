from django.contrib.auth import logout
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(View):
    def post(self, request: HttpRequest) -> JsonResponse:
        logout(request)
        request.session.flush()
        return JsonResponse({"logged_out": True})
