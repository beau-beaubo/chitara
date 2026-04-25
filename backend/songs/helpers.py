import json
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404

from .models import Song


def json_body(request: HttpRequest) -> dict[str, Any]:
    if not request.body:
        return {}
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON body")
    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object")
    return payload


def song_to_dict(song: Song) -> dict[str, Any]:
    return {
        "id": song.id,
        "title": song.title,
        "creator_id": song.creator_id,
        "creation_date": song.creation_date.isoformat() if song.creation_date else None,
        "file_path": song.file_path,
        "file_type": song.file_type,
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


def require_auth(request: HttpRequest) -> JsonResponse | None:
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    return None


def get_owned_song_or_404(request: HttpRequest, song_id: int) -> Song:
    return get_object_or_404(Song, pk=song_id, creator=request.user)


def generation_to_dict(result: Any) -> dict[str, Any]:
    return {
        "task_id": getattr(result, "task_id", None),
        "status": getattr(result, "status", None),
        "audio_url": getattr(result, "audio_url", None),
        "stream_audio_url": getattr(result, "stream_audio_url", None),
        "duration_seconds": getattr(result, "duration_seconds", None),
        "title": getattr(result, "title", None),
    }
