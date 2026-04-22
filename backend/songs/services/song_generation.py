from __future__ import annotations

from songs.generation import SongGenerationRequest, SongGenerationResult, get_active_song_generator
from songs.models import Song, SongStatus


def start_song_generation(song: Song) -> SongGenerationResult:
    generator = get_active_song_generator()
    request = _build_request(song)
    result = generator.generate(request)
    _apply_result(song, result)
    song.save()
    return result


def refresh_song_generation(song: Song) -> SongGenerationResult:
    if not song.generation_task_id:
        raise ValueError("Song has no generation_task_id; start generation first")

    generator = get_active_song_generator()
    result = generator.get_details(song.generation_task_id)
    _apply_result(song, result)
    song.save()
    return result


def _build_request(song: Song) -> SongGenerationRequest:
    return SongGenerationRequest(
        title=song.title,
        prompt=song.prompt_text,
        voice_type=song.voice_type,
        duration_seconds=song.duration,
    )


def _apply_result(song: Song, result: SongGenerationResult) -> None:
    song.generation_task_id = result.task_id
    song.status = _map_generation_status(result.status)

    if result.audio_url:
        song.file_path = result.audio_url

    duration_int = _duration_to_int(result.duration_seconds)
    if duration_int is not None:
        song.duration = duration_int


def _map_generation_status(status: str) -> str:
    normalized = str(status or "").upper().strip()

    if normalized == "SUCCESS":
        return SongStatus.COMPLETED

    if normalized in {"PENDING"}:
        return SongStatus.PENDING

    if normalized in {"TEXT_SUCCESS", "FIRST_SUCCESS", "GENERATING"}:
        return SongStatus.PROCESSING

    if normalized in {
        "FAILED",
        "CREATE_TASK_FAILED",
        "GENERATE_AUDIO_FAILED",
        "CALLBACK_EXCEPTION",
        "SENSITIVE_WORD_ERROR",
    }:
        return SongStatus.FAILED

    if normalized.endswith("_FAILED"):
        return SongStatus.FAILED

    # Default to processing for unknown intermediate states.
    return SongStatus.PROCESSING


def _duration_to_int(duration_seconds: float | None) -> int | None:
    if duration_seconds is None:
        return None
    try:
        value = int(round(float(duration_seconds)))
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None
