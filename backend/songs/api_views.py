import json
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import GenreTag, MoodTag, OccasionTag, Song
from .services.song_generation import refresh_song_generation, start_song_generation


def _json_body(request: HttpRequest) -> dict[str, Any]:
    if not request.body:
        return {}
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON body")
    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object")
    return payload


def _song_to_dict(song: Song) -> dict[str, Any]:
    return {
        "id": song.id,
        "title": song.title,
        "creator_id": song.creator_id,
        "creation_date": song.creation_date.isoformat() if song.creation_date else None,
        "file_path": song.file_path,
        "generation_task_id": song.generation_task_id,
        "status": song.status,
        "prompt_text": song.prompt_text,
        "voice_type": song.voice_type,
        "duration": song.duration,
        "is_shared": song.is_shared,
        "share_hash": song.share_hash,
        "genre_ids": list(song.genres.values_list("id", flat=True)),
        "mood_ids": list(song.moods.values_list("id", flat=True)),
        "occasion_ids": list(song.occasions.values_list("id", flat=True)),
    }


def _generation_to_dict(result: Any) -> dict[str, Any]:
    return {
        "task_id": getattr(result, "task_id", None),
        "status": getattr(result, "status", None),
        "audio_url": getattr(result, "audio_url", None),
        "stream_audio_url": getattr(result, "stream_audio_url", None),
        "duration_seconds": getattr(result, "duration_seconds", None),
        "title": getattr(result, "title", None),
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
def songs_list_create(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        songs = Song.objects.all().order_by("-creation_date")
        return JsonResponse({"results": [_song_to_dict(song) for song in songs]})

    try:
        payload = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    required_fields = ["title", "creator_id", "prompt_text", "voice_type"]
    missing_fields = [
        field
        for field in required_fields
        if field not in payload or payload[field] is None or payload[field] == ""
    ]
    if missing_fields:
        return JsonResponse(
            {
                "error": "Missing required fields",
                "missing": missing_fields,
                "required": required_fields,
            },
            status=400,
        )

    title = payload["title"]
    creator_id = payload["creator_id"]
    prompt_text = payload["prompt_text"]
    voice_type = payload["voice_type"]

    if not isinstance(creator_id, int) or creator_id <= 0:
        return JsonResponse(
            {"error": "creator_id must be a positive integer"},
            status=400,
        )

    User = get_user_model()
    creator = get_object_or_404(User, pk=creator_id)

    song = Song.objects.create(
        title=title,
        creator=creator,
        prompt_text=prompt_text,
        voice_type=voice_type,
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

    return JsonResponse(_song_to_dict(song), status=201)


@csrf_exempt
@require_http_methods(["GET", "PATCH", "PUT", "DELETE"])
def songs_detail(request: HttpRequest, song_id: int) -> JsonResponse:
    song = get_object_or_404(Song, pk=song_id)

    if request.method == "GET":
        return JsonResponse(_song_to_dict(song))

    if request.method == "DELETE":
        song.delete()
        return JsonResponse({"deleted": True})

    try:
        payload = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    # Scalar fields
    updatable_fields = {
        "title",
        "status",
        "file_path",
        "duration",
        "is_shared",
        "share_hash",
        "prompt_text",
        "voice_type",
    }
    for field_name in updatable_fields:
        if field_name in payload:
            setattr(song, field_name, payload[field_name])

    # creator change
    if "creator_id" in payload:
        User = get_user_model()
        song.creator = get_object_or_404(User, pk=payload["creator_id"])

    song.save()

    # M2M updates
    if "genre_ids" in payload and isinstance(payload["genre_ids"], list):
        song.genres.set(GenreTag.objects.filter(id__in=payload["genre_ids"]))
    if "mood_ids" in payload and isinstance(payload["mood_ids"], list):
        song.moods.set(MoodTag.objects.filter(id__in=payload["mood_ids"]))
    if "occasion_ids" in payload and isinstance(payload["occasion_ids"], list):
        song.occasions.set(OccasionTag.objects.filter(id__in=payload["occasion_ids"]))

    return JsonResponse(_song_to_dict(song))


@csrf_exempt
@require_http_methods(["GET", "POST"])
def songs_generate(request: HttpRequest, song_id: int) -> JsonResponse:
    """Start generation (POST) or poll status (GET) for a Song.

    Strategy is selected centrally via settings/env var (GENERATOR_STRATEGY=mock|suno).
    """

    song = get_object_or_404(Song, pk=song_id)

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
        return JsonResponse(
            {"error": "Generation failed", "details": str(exc)},
            status=502,
        )

    return JsonResponse(
        {"song": _song_to_dict(song), "generation": _generation_to_dict(result)},
        status=status_code,
    )
