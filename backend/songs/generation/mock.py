from __future__ import annotations

import hashlib

from .base import SongGenerationRequest, SongGenerationResult, SongGeneratorStrategy


class MockSongGeneratorStrategy(SongGeneratorStrategy):
    """Offline deterministic generator for development/testing."""

    def __init__(self, *, audio_url_prefix: str = "mock://audio/") -> None:
        self._audio_url_prefix = audio_url_prefix

    def generate(self, request: SongGenerationRequest) -> SongGenerationResult:
        task_id = self._make_task_id(request)
        audio_url = f"{self._audio_url_prefix}{task_id}.mp3"
        return SongGenerationResult(
            task_id=task_id,
            status="SUCCESS",
            audio_url=audio_url,
            duration_seconds=120.0,
            title=request.title or "Mock Song",
            raw={"strategy": "mock"},
        )

    def get_details(self, task_id: str) -> SongGenerationResult:
        audio_url = f"{self._audio_url_prefix}{task_id}.mp3"
        return SongGenerationResult(
            task_id=task_id,
            status="SUCCESS",
            audio_url=audio_url,
            duration_seconds=120.0,
            title="Mock Song",
            raw={"strategy": "mock"},
        )

    @staticmethod
    def _make_task_id(request: SongGenerationRequest) -> str:
        stable_key = "|".join(
            [
                request.title,
                request.prompt,
                request.voice_type or "",
                str(request.duration_seconds or ""),
            ]
        )
        digest = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()[:12]
        return f"mock_{digest}"
