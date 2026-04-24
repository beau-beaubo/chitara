from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .base import SongGeneratorStrategy
from .circuit_breaker_song_generator_strategy import CircuitBreakerSongGeneratorStrategy
from .mock import MockSongGeneratorStrategy
from .suno import SunoApiError, SunoConfig, SunoSongGeneratorStrategy


def get_active_song_generator() -> SongGeneratorStrategy:
    strategy = str(getattr(settings, "GENERATOR_STRATEGY", "mock")).lower().strip()

    if strategy == "mock":
        return MockSongGeneratorStrategy()

    if strategy == "suno":
        try:
            config = SunoConfig(
                api_key=str(getattr(settings, "SUNO_API_KEY", "")),
                base_url=str(
                    getattr(settings, "SUNO_API_BASE_URL", "https://api.sunoapi.org/api/v1")
                ),
                model=str(getattr(settings, "SUNO_MODEL", "V4_5ALL")),
                custom_mode=bool(getattr(settings, "SUNO_CUSTOM_MODE", False)),
                instrumental=bool(getattr(settings, "SUNO_INSTRUMENTAL", False)),
                call_back_url=(
                    str(getattr(settings, "SUNO_CALLBACK_URL", "")).strip() or None
                ),
                timeout_seconds=float(getattr(settings, "SUNO_HTTP_TIMEOUT_SECONDS", 30.0)),
            )
            return CircuitBreakerSongGeneratorStrategy(SunoSongGeneratorStrategy(config))
        except (ValueError, SunoApiError) as exc:
            raise ImproperlyConfigured(str(exc)) from exc

    raise ImproperlyConfigured(
        "Unsupported GENERATOR_STRATEGY. Expected 'mock' or 'suno'."
    )
