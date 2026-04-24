from __future__ import annotations

from typing import Any

from .base import SongGenerationRequest, SongGenerationResult, SongGeneratorStrategy
from .suno_api_client import SunoApiClient
from .suno_config import SunoConfig
from .suno_errors import SunoApiError
from .suno_helpers import coerce_float, first_of, first_track


class SunoSongGeneratorStrategy(SongGeneratorStrategy):
    def __init__(self, config: SunoConfig) -> None:
        if not config.api_key:
            raise SunoApiError("Missing Suno API key (set SUNO_API_KEY)")
        self._config = config
        self._client = SunoApiClient(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout_seconds=config.timeout_seconds,
        )

    def generate(self, request: SongGenerationRequest) -> SongGenerationResult:
        prompt = request.prompt.strip()
        if not prompt:
            raise ValueError("prompt is required")

        payload: dict[str, Any] = {
            "prompt": prompt,
            "customMode": bool(self._config.custom_mode),
            "instrumental": bool(self._config.instrumental),
            "model": self._config.model,
        }
        if self._config.call_back_url:
            payload["callBackUrl"] = self._config.call_back_url

        task_id = self._client.generate_music(payload)
        return SongGenerationResult(task_id=task_id, status="PENDING", raw={"payload": payload})

    def get_details(self, task_id: str) -> SongGenerationResult:
        record = self._client.get_record_info(task_id)
        status = str(record.get("status") or "PENDING")

        track = first_track(record)
        audio_url = first_of(track, "audio_url", "audioUrl")
        stream_audio_url = first_of(track, "stream_audio_url", "streamAudioUrl")
        title = first_of(track, "title")
        duration_seconds = coerce_float(first_of(track, "duration"))

        return SongGenerationResult(
            task_id=str(record.get("taskId") or task_id),
            status=status,
            audio_url=audio_url,
            stream_audio_url=stream_audio_url,
            duration_seconds=duration_seconds,
            title=title,
            raw=record,
        )
