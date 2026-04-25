import io
import math
import wave

import requests as http_requests

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from songs.helpers import get_owned_song_or_404, require_auth


@csrf_exempt
@require_http_methods(["GET"])
def songs_download(request: HttpRequest, song_id: int) -> HttpResponse:
    """Download the audio file (creator-only)."""
    auth_error = require_auth(request)
    if auth_error is not None:
        return auth_error

    song = get_owned_song_or_404(request, song_id)
    if not song.file_path:
        return JsonResponse({"error": "Song has no audio file"}, status=400)

    url = str(song.file_path)

    if url.startswith("/api/mock-audio/") and url.endswith(".wav"):
        task_id = url.split("/")[-1].removesuffix(".wav")
        return mock_audio_wav(request, task_id)

    if url.startswith("http://") or url.startswith("https://"):
        try:
            upstream = http_requests.get(url, stream=True, timeout=30)
            upstream.raise_for_status()
            content = upstream.content
        except Exception as exc:
            return JsonResponse({"error": "Download failed", "details": str(exc)}, status=502)

        safe_title = (
            "".join(ch for ch in song.title if ch.isalnum() or ch in {" ", "-", "_"}).strip()
            or "song"
        )
        resp = HttpResponse(content, content_type=upstream.headers.get("Content-Type", "audio/mpeg"))
        resp["Content-Disposition"] = f'attachment; filename="{safe_title}.mp3"'
        return resp

    return JsonResponse({"error": "Unsupported file_path for download"}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def mock_audio_wav(request: HttpRequest, task_id: str) -> HttpResponse:
    """Return a small generated WAV so mock songs are playable."""
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

    response = HttpResponse(buffer.getvalue(), content_type="audio/wav")
    response["Cache-Control"] = "public, max-age=3600"
    response["Content-Disposition"] = f'inline; filename="{task_id}.wav"'
    return response
