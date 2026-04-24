from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SunoConfig:
    api_key: str
    base_url: str = "https://api.sunoapi.org/api/v1"
    model: str = "V4_5ALL"
    custom_mode: bool = False
    instrumental: bool = False
    call_back_url: str | None = None
    timeout_seconds: float = 30.0
