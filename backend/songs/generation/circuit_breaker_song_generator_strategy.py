from __future__ import annotations

from datetime import timedelta

from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from .base import SongGeneratorStrategy


_SUNO_CB_FAIL_COUNT_KEY = "suno_cb_fail_count"
_SUNO_CB_OPEN_UNTIL_KEY = "suno_cb_open_until"
_SUNO_CB_THRESHOLD = 3
_SUNO_CB_COOLDOWN_SECONDS = 60


class CircuitBreakerSongGeneratorStrategy(SongGeneratorStrategy):
    """Small circuit-breaker wrapper for Suno strategy."""

    def __init__(self, inner: SongGeneratorStrategy) -> None:
        self._inner = inner

    def generate(self, request):
        self._raise_if_open()
        return self._call_with_breaker(lambda: self._inner.generate(request))

    def get_details(self, task_id: str):
        self._raise_if_open()
        return self._call_with_breaker(lambda: self._inner.get_details(task_id))

    def _raise_if_open(self) -> None:
        open_until = cache.get(_SUNO_CB_OPEN_UNTIL_KEY)
        if open_until and timezone.now() < open_until:
            raise ImproperlyConfigured("Suno circuit breaker is open; retry shortly")

    def _call_with_breaker(self, fn):
        try:
            result = fn()
        except Exception:
            fail_count = int(cache.get(_SUNO_CB_FAIL_COUNT_KEY, 0)) + 1
            cache.set(_SUNO_CB_FAIL_COUNT_KEY, fail_count, timeout=600)

            if fail_count >= _SUNO_CB_THRESHOLD:
                open_until = timezone.now() + timedelta(seconds=_SUNO_CB_COOLDOWN_SECONDS)
                cache.set(_SUNO_CB_OPEN_UNTIL_KEY, open_until, timeout=_SUNO_CB_COOLDOWN_SECONDS)

            raise

        cache.set(_SUNO_CB_FAIL_COUNT_KEY, 0, timeout=600)
        return result
