from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from songs.models import GenreTag, MoodTag, OccasionTag


@csrf_exempt
@require_http_methods(["GET"])
def tags_list(request: HttpRequest) -> JsonResponse:
    """List available genre/mood/occasion tags for the UI."""
    genres    = list(GenreTag.objects.all().order_by("name").values("id", "name"))
    moods     = list(MoodTag.objects.all().order_by("name").values("id", "name"))
    occasions = list(OccasionTag.objects.all().order_by("name").values("id", "name"))
    return JsonResponse({"genres": genres, "moods": moods, "occasions": occasions})
