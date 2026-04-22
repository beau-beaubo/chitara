from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from .base import SongGenerationRequest, SongGenerationResult, SongGeneratorStrategy


class SunoApiError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SunoConfig:
    api_key: str
    base_url: str = "https://api.sunoapi.org/api/v1"
    model: str = "V4_5ALL"
    custom_mode: bool = False
    instrumental: bool = False
    call_back_url: str | None = None
    timeout_seconds: float = 30.0


class SunoApiClient:
    def __init__(self, *, api_key: str, base_url: str, timeout_seconds: float) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def generate_music(self, payload: dict[str, Any]) -> str:
        url = f"{self._base_url}/generate"
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        body = _safe_json(response)
        _raise_for_api_error(body)
        try:
            return str(body["data"]["taskId"])
        except Exception as exc:  # pragma: no cover
            raise SunoApiError(f"Unexpected Suno generate response: {body!r}") from exc

    def get_record_info(self, task_id: str) -> dict[str, Any]:
        url = f"{self._base_url}/generate/record-info"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            params={"taskId": task_id},
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        body = _safe_json(response)
        _raise_for_api_error(body)
        data = body.get("data")
        if not isinstance(data, dict):
            raise SunoApiError(f"Unexpected Suno record-info response: {body!r}")
        return data


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

        track = _first_track(record)
        audio_url = _first_of(track, "audio_url", "audioUrl")
        stream_audio_url = _first_of(track, "stream_audio_url", "streamAudioUrl")
        title = _first_of(track, "title")
        duration_seconds = _coerce_float(_first_of(track, "duration"))

        return SongGenerationResult(
            task_id=str(record.get("taskId") or task_id),
            status=status,
            audio_url=audio_url,
            stream_audio_url=stream_audio_url,
            duration_seconds=duration_seconds,
            title=title,
            raw=record,
        )


def _safe_json(response: requests.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except Exception as exc:
        raise SunoApiError("Suno API returned invalid JSON") from exc
    if not isinstance(body, dict):
        raise SunoApiError(f"Unexpected Suno API response: {body!r}")
    return body


def _raise_for_api_error(body: dict[str, Any]) -> None:
    code = body.get("code")
    if code == 200:
        return
    msg = body.get("msg")
    raise SunoApiError(f"Suno API error (code={code}): {msg}")


def _first_track(record: dict[str, Any]) -> dict[str, Any]:
    response = record.get("response")
    if not isinstance(response, dict):
        return {}

    tracks = response.get("data")
    if isinstance(tracks, list) and tracks:
        first = tracks[0]
        return first if isinstance(first, dict) else {}

    tracks = response.get("sunoData")
    if isinstance(tracks, list) and tracks:
        first = tracks[0]
        return first if isinstance(first, dict) else {}

    return {}


def _first_of(obj: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = obj.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            return value
        return str(value)
    return None


def _coerce_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
