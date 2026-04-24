from __future__ import annotations

from .base import SongGenerationRequest, SongGenerationResult, SongGeneratorStrategy
from .mock_helpers import make_mock_task_id


class MockSongGeneratorStrategy(SongGeneratorStrategy):
    """Offline deterministic generator for development/testing."""

    def __init__(self, *, audio_url_prefix: str = "/api/mock-audio/") -> None:
        self._audio_url_prefix = audio_url_prefix

    def generate(self, request: SongGenerationRequest) -> SongGenerationResult:
        task_id = make_mock_task_id(request)
        audio_url = f"{self._audio_url_prefix}{task_id}.wav"
        return SongGenerationResult(
            task_id=task_id,
            status="SUCCESS",
            audio_url=audio_url,
            duration_seconds=120.0,
            title=request.title or "Mock Song",
            raw={"strategy": "mock"},
        )

    def get_details(self, task_id: str) -> SongGenerationResult:
        audio_url = f"{self._audio_url_prefix}{task_id}.wav"
        return SongGenerationResult(
            task_id=task_id,
            status="SUCCESS",
            audio_url=audio_url,
            duration_seconds=120.0,
            title="Mock Song",
            raw={"strategy": "mock"},
        )
