import secrets

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from songs.helpers import get_owned_song_or_404, require_auth, song_to_dict


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def songs_share(request: HttpRequest, song_id: int) -> JsonResponse:
    """Create (POST) or revoke (DELETE) a share link for a song."""
    auth_error = require_auth(request)
    if auth_error is not None:
        return auth_error

    song = get_owned_song_or_404(request, song_id)

    if request.method == "DELETE":
        song.is_shared = False
        song.save(update_fields=["is_shared"])
        return JsonResponse({"song": song_to_dict(song), "share_url": None})

    if not song.share_hash:
        song.share_hash = secrets.token_urlsafe(24)
    song.is_shared = True
    song.save(update_fields=["share_hash", "is_shared"])

    return JsonResponse({"song": song_to_dict(song), "share_url": f"/shared/{song.share_hash}"})
