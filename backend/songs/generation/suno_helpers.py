from __future__ import annotations

from typing import Any

import requests

from .suno_errors import SunoApiError


def safe_json(response: requests.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except Exception as exc:
        raise SunoApiError("Suno API returned invalid JSON") from exc
    if not isinstance(body, dict):
        raise SunoApiError(f"Unexpected Suno API response: {body!r}")
    return body


def raise_for_api_error(body: dict[str, Any]) -> None:
    code = body.get("code")
    if code == 200:
        return
    msg = body.get("msg")
    raise SunoApiError(f"Suno API error (code={code}): {msg}")


def first_track(record: dict[str, Any]) -> dict[str, Any]:
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


def first_of(obj: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = obj.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            return value
        return str(value)
    return None


def coerce_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
