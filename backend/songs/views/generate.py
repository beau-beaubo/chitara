from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from songs.helpers import generation_to_dict, get_owned_song_or_404, require_auth, song_to_dict
from songs.services.song_generation import refresh_song_generation, start_song_generation


@csrf_exempt
@require_http_methods(["GET", "POST"])
def songs_generate(request: HttpRequest, song_id: int) -> JsonResponse:
    """Start generation (POST) or poll status (GET) for a Song."""
    auth_error = require_auth(request)
    if auth_error is not None:
        return auth_error

    song = get_owned_song_or_404(request, song_id)

    try:
        if request.method == "POST":
            result = start_song_generation(song)
            status_code = 200 if result.status == "SUCCESS" else 202
        else:
            result = refresh_song_generation(song)
            status_code = 200
    except ImproperlyConfigured as exc:
        return JsonResponse({"error": str(exc)}, status=500)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception as exc:
        return JsonResponse({"error": "Generation failed", "details": str(exc)}, status=502)

    return JsonResponse(
        {"song": song_to_dict(song), "generation": generation_to_dict(result)},
        status=status_code,
    )
