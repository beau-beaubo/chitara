import io
import json
import math
import secrets
import wave
from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

import requests

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


def _require_auth(request: HttpRequest) -> JsonResponse | None:
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    return None


def _get_owned_song_or_404(request: HttpRequest, song_id: int) -> Song:
    user = request.user
    return get_object_or_404(Song, pk=song_id, creator=user)


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
    auth_error = _require_auth(request)
    if auth_error is not None:
        return auth_error

    if request.method == "GET":
        songs = Song.objects.filter(creator=request.user).order_by("-creation_date")
        return JsonResponse({"results": [_song_to_dict(song) for song in songs]})

    try:
        payload = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    required_fields = ["title", "prompt_text", "voice_type"]
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
    prompt_text = payload["prompt_text"]
    voice_type = payload["voice_type"]

    creator = request.user

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
    auth_error = _require_auth(request)
    if auth_error is not None:
        return auth_error

    song = _get_owned_song_or_404(request, song_id)

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

    # creator change is not allowed via API (ownership enforced by auth)

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

    auth_error = _require_auth(request)
    if auth_error is not None:
        return auth_error

    song = _get_owned_song_or_404(request, song_id)

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


@csrf_exempt
@require_http_methods(["GET"])
def tags_list(request: HttpRequest) -> JsonResponse:
    """List available tag options for the UI (genre/mood/occasion)."""

    genres = list(GenreTag.objects.all().order_by("name").values("id", "name"))
    moods = list(MoodTag.objects.all().order_by("name").values("id", "name"))
    occasions = list(OccasionTag.objects.all().order_by("name").values("id", "name"))
    return JsonResponse({"genres": genres, "moods": moods, "occasions": occasions})


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def songs_share(request: HttpRequest, song_id: int) -> JsonResponse:
    """Create (POST) or revoke (DELETE) a share link for a song."""

    auth_error = _require_auth(request)
    if auth_error is not None:
        return auth_error

    song = _get_owned_song_or_404(request, song_id)

    if request.method == "DELETE":
        song.is_shared = False
        song.save(update_fields=["is_shared"])
        return JsonResponse({"song": _song_to_dict(song), "share_url": None})

    if not song.share_hash:
        song.share_hash = secrets.token_urlsafe(24)
    song.is_shared = True
    song.save(update_fields=["share_hash", "is_shared"])

    share_url = f"/shared/{song.share_hash}"
    return JsonResponse({"song": _song_to_dict(song), "share_url": share_url})


@csrf_exempt
@require_http_methods(["GET"])
def shared_song_detail(request: HttpRequest, share_hash: str) -> JsonResponse:
    """Public read-only access to a shared song by share_hash (FR-17)."""

    song = get_object_or_404(Song, share_hash=share_hash, is_shared=True)
    return JsonResponse({"song": _song_to_dict(song)})


@csrf_exempt
@require_http_methods(["GET"])
def songs_download(request: HttpRequest, song_id: int) -> HttpResponse:
    """Download the audio file (creator-only) (FR-18)."""

    auth_error = _require_auth(request)
    if auth_error is not None:
        return auth_error

    song = _get_owned_song_or_404(request, song_id)
    if not song.file_path:
        return JsonResponse({"error": "Song has no audio file"}, status=400)

    url = str(song.file_path)

    if url.startswith("/api/mock-audio/") and url.endswith(".wav"):
        task_id = url.split("/")[-1].removesuffix(".wav")
        return mock_audio_wav(request, task_id)

    if url.startswith("http://") or url.startswith("https://"):
        try:
            upstream = requests.get(url, stream=True, timeout=30)
            upstream.raise_for_status()
            content = upstream.content
        except Exception as exc:
            return JsonResponse({"error": "Download failed", "details": str(exc)}, status=502)

        resp = HttpResponse(content, content_type=upstream.headers.get("Content-Type", "audio/mpeg"))
        safe_title = "".join(ch for ch in song.title if ch.isalnum() or ch in {" ", "-", "_"}).strip() or "song"
        resp["Content-Disposition"] = f'attachment; filename="{safe_title}.mp3"'
        return resp

    return JsonResponse({"error": "Unsupported file_path for download"}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def mock_audio_wav(request: HttpRequest, task_id: str) -> HttpResponse:
    """Return a small generated WAV so mock songs are playable (FR-15)."""

    duration_seconds = 1.5
    sample_rate = 44100
    frequency = 440.0
    amplitude = 0.2

    nframes = int(duration_seconds * sample_rate)
    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        frames = bytearray()
        for i in range(nframes):
            t = i / sample_rate
            value = amplitude * math.sin(2 * math.pi * frequency * t)
            sample = int(max(-1.0, min(1.0, value)) * 32767)
            frames.extend(sample.to_bytes(2, byteorder="little", signed=True))

        wf.writeframes(frames)

    body = buffer.getvalue()
    response = HttpResponse(body, content_type="audio/wav")
    response["Cache-Control"] = "public, max-age=3600"
    response["Content-Disposition"] = f'inline; filename="{task_id}.wav"'
    return response
