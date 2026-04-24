from __future__ import annotations

from typing import Any

import requests

from .suno_errors import SunoApiError
from .suno_helpers import raise_for_api_error, safe_json


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
        body = safe_json(response)
        raise_for_api_error(body)
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
        body = safe_json(response)
        raise_for_api_error(body)
        data = body.get("data")
        if not isinstance(data, dict):
            raise SunoApiError(f"Unexpected Suno record-info response: {body!r}")
        return data
