from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from songs.helpers import song_to_dict
from songs.models import Song


@csrf_exempt
@require_http_methods(["GET"])
def shared_song_detail(request: HttpRequest, share_hash: str) -> JsonResponse:
    """Public read-only access to a shared song by share_hash."""
    song = get_object_or_404(Song, share_hash=share_hash, is_shared=True)
    return JsonResponse({"song": song_to_dict(song)})
