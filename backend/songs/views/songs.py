from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from songs.helpers import get_owned_song_or_404, json_body, require_auth, song_to_dict
from songs.models import GenreTag, MoodTag, OccasionTag, Song


@csrf_exempt
@require_http_methods(["GET", "POST"])
def songs_list_create(request: HttpRequest) -> JsonResponse:
    auth_error = require_auth(request)
    if auth_error is not None:
        return auth_error

    if request.method == "GET":
        songs = Song.objects.filter(creator=request.user).order_by("-creation_date")
        return JsonResponse({"results": [song_to_dict(s) for s in songs]})

    try:
        payload = json_body(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    required_fields = ["title", "prompt_text", "voice_type"]
    missing = [f for f in required_fields if not payload.get(f)]
    if missing:
        return JsonResponse({"error": "Missing required fields", "missing": missing}, status=400)

    song = Song.objects.create(
        title=payload["title"],
        creator=request.user,
        prompt_text=payload["prompt_text"],
        voice_type=payload["voice_type"],
        status=payload.get("status", Song._meta.get_field("status").default),
        file_path=payload.get("file_path"),
        duration=payload.get("duration"),
        is_shared=bool(payload.get("is_shared", False)),
        share_hash=payload.get("share_hash"),
    )

    genre_ids = payload.get("genre_ids")
    mood_ids = payload.get("mood_ids")
    occasion_ids = payload.get("occasion_ids")

    if isinstance(genre_ids, list):
        song.genres.set(GenreTag.objects.filter(id__in=genre_ids))
    if isinstance(mood_ids, list):
        song.moods.set(MoodTag.objects.filter(id__in=mood_ids))
    if isinstance(occasion_ids, list):
        song.occasions.set(OccasionTag.objects.filter(id__in=occasion_ids))

    return JsonResponse(song_to_dict(song), status=201)


@csrf_exempt
@require_http_methods(["GET", "PATCH", "PUT", "DELETE"])
def songs_detail(request: HttpRequest, song_id: int) -> JsonResponse:
    auth_error = require_auth(request)
    if auth_error is not None:
        return auth_error

    song = get_owned_song_or_404(request, song_id)

    if request.method == "GET":
        return JsonResponse(song_to_dict(song))

    if request.method == "DELETE":
        song.delete()
        return JsonResponse({"deleted": True})

    try:
        payload = json_body(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    updatable_fields = {"title", "status", "file_path", "duration",
                        "is_shared", "share_hash", "prompt_text", "voice_type"}
    for field_name in updatable_fields:
        if field_name in payload:
            setattr(song, field_name, payload[field_name])
    song.save()

    if "genre_ids" in payload and isinstance(payload["genre_ids"], list):
        song.genres.set(GenreTag.objects.filter(id__in=payload["genre_ids"]))
    if "mood_ids" in payload and isinstance(payload["mood_ids"], list):
        song.moods.set(MoodTag.objects.filter(id__in=payload["mood_ids"]))
    if "occasion_ids" in payload and isinstance(payload["occasion_ids"], list):
        song.occasions.set(OccasionTag.objects.filter(id__in=payload["occasion_ids"]))

    return JsonResponse(song_to_dict(song))
